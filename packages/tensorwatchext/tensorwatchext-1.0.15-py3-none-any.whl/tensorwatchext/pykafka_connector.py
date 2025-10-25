from pykafka import KafkaClient
from pykafka.common import OffsetType
from .watcher import Watcher

import threading
from queue import Queue

#imported parsers here that need no install
import json
import pickle
try:
    import xmltodict as xmltodict   
except:
    pass
try:
    import avro.schema
    from avro.io import DatumReader
    import io
    from avro.io import BinaryDecoder
except:
    pass
try:
    from protobuf_to_dict import protobuf_to_dict
except:
    pass
from datetime import datetime
import time
import random

def get_ioloop():
    import IPython, zmq
    ipython = IPython.get_ipython()
    if ipython and hasattr(ipython, 'kernel'):
        return zmq.eventloop.ioloop.IOLoop.instance()
from probables import (CountMinSketch)

#The IOloop is shared
ioloop = get_ioloop()

# def run_progress(hosts:str=None, topic:str=None, parsetype:str=None, parser_extra:str=None, queue_length:int=None):
#         thread = kafka_contector(hosts,topic,parsetype,parser_extra,queue_length)
#         print("test")
#         return
#         # return thread

# from pykafka.exceptions import SocketDisconnectedError, LeaderNotAvailable
# # this illustrates consumer error catching;
# consumer = topic.get_simple_consumer()
# try:
#     consumer.consume()
# except (SocketDisconnectedError) as e:
#     consumer = topic.get_simple_consumer()
#     # use either the above method or the following:
#     consumer.stop()
#     consumer.start()

class pykafka_connector(threading.Thread):
                
    def quit(self):
        self._quit.set()        

    def __init__(self, hosts:str=None, topic:str=None, parsetype:str=None, parser_extra:str=None, queue_length:int=None, cluster_size:int=1,
    twapi_instance=None,
    #pykfka settings        
    cluster:str=None, consumer_group:bytes=bytes("default", 'utf-8'), partitions:str=None, probuf_message:str=None, zookeeper_hosts:str='127.0.0.1:2181',
    fetch_message_max_bytes:int=1024 * 1024, num_consumer_fetchers:int=1, auto_commit_enable:bool=False,
    auto_commit_interval_ms:int=60 * 1000, queued_max_messages:int=2000, fetch_min_bytes:int=1,  fetch_error_backoff_ms:int=500, fetch_wait_max_ms:int=100,
    offsets_channel_backoff_ms:int=1000, offsets_commit_max_retries:int=5, auto_offset_reset:OffsetType=OffsetType.EARLIEST, consumer_timeout_ms:int=-1, auto_start:bool=True,
    reset_offset_on_start:bool=False, compacted_topic:bool=False, generation_id:int=-1, consumer_id:bool=b'',  reset_offset_on_fetch:bool=True, decode:str="utf-8", 
    scema_path:str=None, random_sampling:int=None, countmin_width:int=None, countmin_depth:int=None, **kwargs):#deserializer:function=None,
        super().__init__()
        self.hosts = hosts
        self.topic = topic
        self.cluster_size=cluster_size
        self.decode = decode
        self.twapi_instance = twapi_instance
        self.size=0
        self.kafka_thread = None
        self.parsetype = parsetype
        self.scema_path = scema_path
        self.random_sampling = random_sampling
        # self.schema=schema
        self.parser_extra = parser_extra
        self.queue_length = queue_length
        if self.queue_length is None:
            self.data=Queue(maxsize=50000)
        else:
            self.data=Queue(maxsize=self.queue_length)
        self._quit = threading.Event()
        # self._quit = threading.Event()
        #pykfka
        self.cluster, self.consumer_group, self.partitions, self.zookeeper_hosts = cluster, consumer_group, partitions, zookeeper_hosts
        self.fetch_message_max_bytes, self.num_consumer_fetchers = \
            fetch_message_max_bytes, num_consumer_fetchers
        self.auto_commit_enable, self.auto_commit_interval_ms, self.queued_max_messages, self.fetch_min_bytes, self.fetch_error_backoff_ms = \
            auto_commit_enable, auto_commit_interval_ms, queued_max_messages, fetch_min_bytes, fetch_error_backoff_ms
        self.fetch_wait_max_ms, self.offsets_channel_backoff_ms, self.offsets_commit_max_retries, self.auto_offset_reset, self.consumer_timeout_ms = \
            fetch_wait_max_ms, offsets_channel_backoff_ms, offsets_commit_max_retries, auto_offset_reset, consumer_timeout_ms
        self.auto_start, self.reset_offset_on_start, self.compacted_topic, self.generation_id, self.consumer_id, self.reset_offset_on_fetch= \
            auto_start, reset_offset_on_start, compacted_topic, generation_id, consumer_id, reset_offset_on_fetch
        # self.deserializer = deserializer
        #memory optimazation limiting the number of stored data
        self.cms={}
        self.countmin_depth = countmin_depth
        self.countmin_width = countmin_width
        self.random_sampling = random_sampling
        #to skip decoders from needed to be install 
        if self.parsetype.lower()=='avro':
            try:
                schema = avro.schema.parse(parser_extra)
                self.reader = DatumReader(schema)
            except: 
                print("avro schema error or avro not installed"+ json.loads(parser_extra))
                return
        elif self.parsetype.lower()=='protobuf' :
            try:
                import sys
                import importlib
                sys.path.append(scema_path)#scema_path change them
                mymodule = importlib.import_module(parser_extra)
                method_to_call = getattr(mymodule, probuf_message)
                self.mymodule = method_to_call()
            except: 
                print("Error importing protobuf")
        self.start()

    #trying to add deferent libraries for deserializing the kafka messages
    def myparser(self,message):#,parsetype=None,parser_extra=None):
        if self.parsetype is None or self.parsetype.lower()=='json' :
            return json.loads(message)
        elif self.parsetype.lower()=='pickle' :
            return pickle.loads(message)
        elif self.parsetype.lower()=='xml' :
            try:
                xml = xmltodict.parse(message)
                return xml["root"]
            except Exception as ex: # pylint: disable=broad-except
                print('Exception occured : ' + message)
        elif self.parsetype.lower()=='protobuf' :
            try:
                temp_message=self.mymodule
                temp_message.ParseFromString(message)
                my_message_dict = protobuf_to_dict(temp_message)
                return my_message_dict
            except:
                print("Error on protobuff parser")
        elif self.parsetype.lower()=='avro' :
            try:
                message_bytes = io.BytesIO(message)
                decoder = BinaryDecoder(message_bytes)
                event_dict = self.reader.read(decoder)
                print(event_dict)
                return event_dict
            except:
                print("Avro error ,perhpas avro not installed")
        return 'error:unkown type of parsing'

    def consumer(self):
        print("consumer start")
        if self.hosts is None:
            client = KafkaClient(hosts="127.0.0.1:9092")
        else:
            client = KafkaClient(hosts=self.hosts)
        topic = client.topics[self.topic]
        consumer = topic.get_balanced_consumer(consumer_group=self.consumer_group, fetch_message_max_bytes=self.fetch_message_max_bytes,zookeeper_hosts=self.zookeeper_hosts,
        num_consumer_fetchers=self.num_consumer_fetchers, auto_commit_enable=self.auto_commit_enable, auto_commit_interval_ms=self.auto_commit_interval_ms, queued_max_messages=self.queued_max_messages, 
        fetch_min_bytes=self.fetch_min_bytes, fetch_error_backoff_ms=self.fetch_error_backoff_ms, fetch_wait_max_ms=self.fetch_wait_max_ms, offsets_channel_backoff_ms=self.offsets_channel_backoff_ms, 
        offsets_commit_max_retries=self.offsets_commit_max_retries, auto_offset_reset=self.auto_offset_reset, consumer_timeout_ms=self.consumer_timeout_ms, auto_start=self.auto_start,
        reset_offset_on_start=self.reset_offset_on_start, compacted_topic=self.compacted_topic, generation_id=self.generation_id, consumer_id=self.consumer_id, reset_offset_on_fetch=self.reset_offset_on_fetch )
        for message in consumer:
            if message is not None:
                if self.random_sampling is not None and self.random_sampling>random.randint(0,100):
                    pass
                else:
                    temp=self.myparser(message.value)#,parsetype)
                    # print(temp)
                    print("wtf is going on")
                    self.data.put(temp)
                    self.size+=1
                    try:
                        if type(temp) is dict and self.countmin_depth is not None and self.countmin_width is not None:
                            # print("it is dict")
                            for key in temp:
                                # print(key)
                                if key not in self.cms.keys():
                                    try:
                                        self.cms[key] = CountMinSketch(width=self.countmin_width, depth=self.countmin_depth)
                                    except:
                                        print("self.cms[key] is None")
                                try:
                                    self.cms[key].add(str(temp[key]))
                                except:
                                    print("self.cms[key].add(str(temp[key]))")
                        elif type(temp) is list and self.countmin_depth is not None and self.countmin_width is not None:
                            for key in temp:
                                if self.cms[key] is None:
                                    self.cms[str(key)] = CountMinSketch(width=self.countmin_width, depth=self.countmin_depth)
                                self.cms[str(key)].add(str(temp[str(key)]))                        
                    except:
                        print("cms assigment error")

    def run(self):
        # kafkaext='confluent'
        # kafkaext='pykfka'
        w = Watcher()
        #queue_length is the maximum messages that will be kept in memory
        if self.cluster_size==1:
            if self.hosts is None:
                client = KafkaClient(hosts="127.0.0.1:9092")
            else:
                client = KafkaClient(hosts=self.hosts)
            topic = client.topics[self.topic]
            consumer = topic.get_simple_consumer(fetch_message_max_bytes=self.fetch_message_max_bytes,
            num_consumer_fetchers=self.num_consumer_fetchers, auto_commit_enable=self.auto_commit_enable, auto_commit_interval_ms=self.auto_commit_interval_ms, queued_max_messages=self.queued_max_messages, 
            fetch_min_bytes=self.fetch_min_bytes, fetch_error_backoff_ms=self.fetch_error_backoff_ms, fetch_wait_max_ms=self.fetch_wait_max_ms, offsets_channel_backoff_ms=self.offsets_channel_backoff_ms, 
            offsets_commit_max_retries=self.offsets_commit_max_retries, auto_offset_reset=self.auto_offset_reset, consumer_timeout_ms=self.consumer_timeout_ms, auto_start=self.auto_start,
            reset_offset_on_start=self.reset_offset_on_start, compacted_topic=self.compacted_topic, generation_id=self.generation_id, consumer_id=self.consumer_id, reset_offset_on_fetch=self.reset_offset_on_fetch )
            for message in consumer:
                if message is not None:
                    if self.random_sampling is not None and self.random_sampling>random.randint(0,100):
                        pass
                    else:
                        temp=self.myparser(message.value)#,parsetype)
                        self.data.put(temp)
                        self.size+=1
                        try:
                            if type(temp) is dict and self.countmin_depth is not None and self.countmin_width is not None:
                                for key in temp:
                                    if key not in self.cms.keys():
                                        try:
                                            self.cms[key] = CountMinSketch(width=self.countmin_width, depth=self.countmin_depth)
                                        except:
                                            print("self.cms[key] is None")
                                    try:
                                        self.cms[key].add(str(temp[key]))
                                    except:
                                        print("self.cms[key].add(str(temp[key]))")
                            elif type(temp) is list and self.countmin_depth is not None and self.countmin_width is not None:
                                for key in temp:
                                    if self.cms[key] is None:
                                        self.cms[str(key)] = CountMinSketch(width=self.countmin_width, depth=self.countmin_depth)
                                    self.cms[str(key)].add(str(temp[str(key)]))                        
                        except:
                            print("cms assigment error")
                        w.observe(data=list(self.data.queue), size=self.size, cms=self.cms)
                        if self.twapi_instance and not self.twapi_instance.first_message_received:
                            self.twapi_instance.enable_apply_buttons()
                            self.twapi_instance.first_message_received = True
        else:
            thread=[] 
            for x in range(self.cluster_size):
                thread.append(threading.Thread(target = self.consumer, args=()))
                thread[x].daemon = True
                thread[x].start()
            while True:
                w.observe(data=list(self.data.queue), size=self.size, cms=self.cms)
                if self.twapi_instance and not self.twapi_instance.first_message_received:
                    self.twapi_instance.enable_apply_buttons()
                    self.twapi_instance.first_message_received = True
                time.sleep(0.5)