import pprint
import re
import json
import jsonpickle

DBG = 0


class PjsuaNetMatrics:
    def __init__(self, name, min, avg, max):
        self.type = name
        self.min = min
        self.avg = avg
        self.max = max


class PjsuaMediaMatrics:
    def __init__(self, id, media_type, codec, sample_rate, peer_ip, rx, tx):
        self.id = id
        self.media_type = media_type
        self.codec = codec
        self.sample_rate = sample_rate
        self.peer_ip = peer_ip
        self.rx = rx
        self.tx = tx


class PjsuaLogParser:
    def __init__(self):
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
                r"#(\d+) (\w+) (\w+) @(\w+), (\w+), peer=([\w\d\.:]+)", data[i])

            if call_time_match:
                self.call_time = call_time_match.groups()[0]

            if media_match:
                media_id, media_type, codec, sample_rate, media_attr, peer_ip = media_match.groups()

                # next list contain the media message
                i += 1

                rx_data = data[i][2]
                tx_data = data[i][4]

                rx_loss_match = re.match(
                    r"loss period:\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", rx_data[3])
                tx_loss_match = re.match(
                    r"loss period:\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", tx_data[3])

                rx = PjsuaNetMatrics(
                    "rx packet loss period", *rx_loss_match.groups())
                tx = PjsuaNetMatrics(
                    "tx packet loss period", *tx_loss_match.groups())

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
            content = line.strip()
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
    FILE = './test.log'
    f = open(FILE, 'r')

    pp = pprint.PrettyPrinter(indent=4)
    parser = PjsuaLogParser()
    parser.parseIndent(f.readlines())

    pp.pprint(parser.toJSON())
    # print(parser.toJSON())
