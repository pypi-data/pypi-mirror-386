# Overspeed

A Multi Port, Multi Process, Multi Coroutine, High Concurrency Project That Integrates Http, Websocket, System Resource Monitoring, And Detailed Logging.

## Installation

```bash
pip install Overspeed

import os as Os;
import Overspeed;

def Http(Context) :
	pass;

def Websocket(Context) :
	pass;

Overspeed.Lunch(
	Proctitle = 'Overspeed' ,
	
	Root_Path = Os.path.dirname(__file__) ,
	
	Http_Status = True ,
	Http_Callable = Http ,
	
	Websocket_Status = True ,
	Websocket_Callable = Websocket ,
);
```

## Pressure Measurement
```
Overspeed

Running 10s test @ http://127.0.0.1:1007/
	1000 threads and 1000 connections
		Thread Stats   Avg      Stdev     Max   +/- Stdev
			Latency   169.32ms  343.33ms   1.94s    88.87%
			Req/Sec    16.79     20.98   101.00     85.86%
	28427 requests in 10.11s, 2.47MB read
	Socket errors: connect 0, read 389, write 0, timeout 579
	Requests/sec:   2813.09
	Transfer/sec:    249.99KB

Flask
gunicorn -w 4 -b 0.0.0.0:8000 flask_app:app

Running 10s test @ http://127.0.0.1:1007/
	1000 threads and 1000 connections
		Thread Stats   Avg      Stdev     Max   +/- Stdev
			Latency   121.17ms  238.08ms   1.74s    92.53%
			Req/Sec     8.74     10.40    50.00     82.00%
	10115 requests in 10.10s, 1.53MB read
	Socket errors: connect 0, read 0, write 0, timeout 55
	Requests/sec:   1001.24
	Transfer/sec:    154.63KB

FastAPI
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4

Running 10s test @ http://127.0.0.1:1007/
	1000 threads and 1000 connections
		Thread Stats   Avg      Stdev     Max   +/- Stdev
			Latency   156.08ms  338.01ms   1.90s    91.46%
			Req/Sec    16.06     19.90   111.00     87.27%
	23774 requests in 10.10s, 2.97MB read
	Socket errors: connect 0, read 397, write 0, timeout 484
	Requests/sec:   2353.04
	Transfer/sec:    301.02KB


Django
gunicorn -w 4 -b 0.0.0.0:8000 myproject.wsgi

Running 10s test @ http://127.0.0.1:1007/
	1000 threads and 1000 connections
		Thread Stats   Avg      Stdev     Max   +/- Stdev
			Latency   153.89ms  270.51ms   1.80s    90.15%
			Req/Sec     7.15      8.87    50.00     86.46%
	7840 requests in 10.10s, 2.23MB read
	Socket errors: connect 0, read 0, write 0, timeout 92
	Requests/sec:    776.04
	Transfer/sec:    225.79KB
```

## Parameter Explain
```
########################################################################################################################

Proctitle = 'Overspeed'; 进程名称

Root_Path = Library.Os.getcwd(); 项目根路径【重要，存放证书和日志等文件】

Http_Status = True; 服务开关
Http_Print = False; 日志打印开关
Http_Journal = True; 日志记录开关
Http_Cpu = 1; 核心倍数
Http_Port = [31100]; 端口
Http_Large = 2097152; 请求体容量
Http_Keyfile = str(); SSL CERT 文件路径
Http_Certfile = str(); SSL KEY 文件路径
Http_Callable = None; 回调函数

Websocket_Status = True; 服务开关
Websocket_Print = False; 日志打印开关
Websocket_Journal = True; 日志记录开关
Websocket_Cpu = 1; 核心倍数
Websocket_Port = [31200]; 端口
Websocket_Timeout = 5; 最长请求间隔，当为0时不自动断开
Websocket_Connect = 60; 最长链接时间，当为0时不自动断开
Websocket_Keyfile = str(); SSL CERT 文件路径
Websocket_Certfile = str(); SSL KEY 文件路径
Websocket_Callable = None; 回调函数

Resource_Status = True; 服务开关
Resource_Print = False; 日志打印开关
Resource_Journal = True; 日志记录开关
Resource_Sleep = 30; 监控间隔时间
Resource_Cpu = True; 核心监控开关
Resource_Memory = True; 内存监控开关
Resource_Network = True; 网络监控开关
Resource_Disk = True; 磁盘监控开关
Resource_File = True; 文件监控开关
Resource_Load = True; 负载监控开关

Journal_Thread = 100; 线程并发数
Journal_Clean = 7; 清理日志天数

Runtime_Trace = '/Runtime/Trace/'; 错误信息路径
Runtime_Http = '/Runtime/Http/'; HTTP信息路径
Runtime_Websocket = '/Runtime/Websocket/'; WEBSOCKET信息路径
Runtime_Resource = '/Runtime/Resource/'; 资源监控信息路径

########################################################################################################################
```