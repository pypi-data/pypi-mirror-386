import paho.mqtt.client as mqtt
import traceback
import getpass
import threading


class MQTT(object):
    def __init__(self, addr='bender.us.es', port=1883, timeout=5, topics2suscribe=None, on_message=None, on_disconnect=None,user=None,password=None):
        username =getpass.getuser()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, username)

        if topics2suscribe is None:
            topics2suscribe = []
        self.topics2suscribe = topics2suscribe

        if on_message is None:
            self.on_message = self.on_message
        else:
            self.on_message = on_message

        if on_disconnect is None:
            self.on_disconnect = self.on_disconnect
        else:
            self.on_disconnect = on_disconnect
        # Con esto se puede mejorar la seguridad del MQTT si el broker esta configurado para eso
        # self.client.username_pw_set(user, password)
        self._mqtt_thread = threading.Thread(target=self.mqtt_thread, args=(addr, port, timeout,))
        self._mqtt_thread.start()

    def mqtt_thread(self, addr='bender.us.es', port=1883, timeout=5):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        try:
            self.client.connect(addr, port, timeout)
        except ConnectionRefusedError:
            print(f"Connection to MQTT server was refused")
            return
        except OSError:
            print(f"MQTT server was not found")
            return
        except TimeoutError:
            print(f"MQTT was busy, timeout error")
            return
        except:
            error = traceback.format_exc()
            print(f"MQTT connection failed, unknown error:\n {error}")
            return
        self.client.loop_forever()
    
    def on_connect(client, userdata, flags, rc):
        print(f"Client {userdata} connected! " + str(rc))

    def on_connect(self,  _client, userdata, flags, rc, properties):
        print("Connected to MQTT server")
        for topic in self.topics2suscribe:
            self.client.subscribe(topic)

    def on_disconnect(self, client, userdata, flags, rc ,properties):
        print("client disconnected ok")

    @staticmethod
    def on_message(_client, user_data, msg):
        message = bool(msg.payload)
        print(message)

    def send_new_msg(self, msg, topic="coordinator"):
        #while not self.client.is_connected():
            #continue
        self.client.publish(topic, msg)

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()