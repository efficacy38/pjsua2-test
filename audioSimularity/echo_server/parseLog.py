import pprint
import re
import json
import jsonpickle

DBG = 0


class PjsuaNetMatrics:
    def __init__(self, name, pkt_loss_min, pkt_loss_avg, pkt_loss_max, total_packet_cnt, total_packet_size):
        self.type = name
        self.pkt_loss_min = pkt_loss_min
        self.pkt_loss_avg = pkt_loss_avg
        self.pkt_loss_max = pkt_loss_max
        self.total_packet_cnt = total_packet_cnt
        self.total_packet_size = total_packet_size


class PjsuaMediaMatrics:
    def __init__(self, id: int, media_type: str, codec: str, sample_rate: str, peer_ip: str, rx: PjsuaNetMatrics, tx: PjsuaNetMatrics):
        self.id = id
        self.media_type = media_type
        self.codec = codec
        self.sample_rate = sample_rate
        self.peer_ip = peer_ip
        self.rx = rx
        self.tx = tx


class PjsuaLogParser:
    def __init__(self, call_id):
        self.call_id = call_id
        self.call_status = None
        self.media = {}
        self.dst_URI = None
        self.call_time = None

    def toJSON(self):
        return json.loads(str(jsonpickle.encode(self, unpicklable=False)))
        # return jsonpickle.encode(self)

    def _update(self, data):
        # unpack the data
        data = data[0]

        # first line has the call status
        call_status_match = re.match(r"\[(.*)\]\ To: (.*)", data[0])
        if call_status_match:
            self.call_status, self.dst_URI = call_status_match.groups()

        # process the media part, and call time period part
        data = data[1]

        i = 0
        while i < len(data):

            # only media has list
            if isinstance(data[i], list):
                raise ValueError(
                    'data get list, expect string: {}'.format(data[i]))

            call_time_match = re.match(
                r"Call time: (\d{2}h:\d{2}m:\d{2}s), \d+st res in \d+ ms, conn in \d+ms", data[i])
            media_match = re.match(
                r"#(\d+) (\w+) (\w+) @(\w+), (\w+), peer=([\w\d\.:-]+)", data[i])

            if call_time_match:
                self.call_time = call_time_match.groups()[0]

            if media_match:
                media_id, media_type, codec, sample_rate, media_attr, peer_ip = media_match.groups()

                # next list contain the media message
                i += 1

                rx_data = data[i][2]
                tx_data = data[i][4]

                rx_loss_match = re.match(
                    r"loss period:\s+([\d.]+)\s+([\d.]+)\s+([\d\.]+)", rx_data[3])
                tx_loss_match = re.match(
                    r"loss period:\s+([\d.]+)\s+([\d.]+)\s+([\d\.]+)", tx_data[3])

                # print(rx_data[0])
                # print(re.findall(r"total (\d+)pkt [\d\.]*.{0,1}B \(([\d\.^\ ]+).{0,1}B", rx_data[0])[0])
                rx_packets_cnt = rx_packets_size = tx_packets_cnt = tx_packets_size ="0kB" 
                try:
                    rx_packets_cnt, rx_packets_size = re.findall(r"total ([\d\.]+\w{0,1})pkt [\d\.]*\w{0,1}B \(([\d\.^\ ]+\w{0,1}B)", rx_data[0])[0]
                    tx_packets_cnt, tx_packets_size = re.findall(r"total ([\d\.]+\w{0,1})pkt [\d\.]*\w{0,1}B \(([\d\.^\ ]+\w{0,1}B)", tx_data[0])[0]
                except Exception as e:
                    print(e.args)


                rx = PjsuaNetMatrics(
                    "rx packet loss period", *rx_loss_match.groups(), rx_packets_cnt, rx_packets_size)
                tx = PjsuaNetMatrics(
                    "tx packet loss period", *tx_loss_match.groups(), tx_packets_cnt, tx_packets_size)

                self.media[media_id] = PjsuaMediaMatrics(
                    media_id, media_type, codec, sample_rate, peer_ip, rx, tx)
            i += 1

    def parseIndent(self, lines):
        if isinstance(lines, str):
            lines = lines.split('\n')
        indentation = []
        data = []
        indentation.append(-1)
        depth = 0
        for line in lines:
            # remove newline and extra-space
            line = line.rstrip()

            # remove indent
            content = line.lstrip()
            # ignore the empty line
            if len(content) == 0:
                continue

            indent = len(line) - len(content)

            if indent > indentation[-1]:
                depth += 1
                indentation.append(indent)
                data.append([])

            elif indent < indentation[-1]:
                while indent < indentation[-1]:
                    depth -= 1
                    indentation.pop()
                    top = data.pop()
                    data[-1].append(top)

                if indent != indentation[-1]:
                    raise RuntimeError("Bad Format")

            data[-1].append(content)
            if DBG:
                print("******** process indent {} ********".format(depth))
                print(content)
                print("******** end process indent {} ********".format(depth))

        # tidy up the unpacked element
        while len(data) > 1:
            top = data.pop()
            data[-1].append(top)

        self._update(data)
        return data


if __name__ == '__main__':
    FILE = './test3.log'
    f = open(FILE, 'r')

    pp = pprint.PrettyPrinter(indent=4)
    parser = PjsuaLogParser("fake-call-id")

    (parser.parseIndent(f.readlines()))

    pp.pprint(parser.toJSON())
    # print(parser.toJSON())
