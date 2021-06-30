@echo off
path = %path%;D:\koala\pd\bin

pd.exe --name=pd2 --client-urls=http://127.0.0.1:2381 --advertise-client-urls=http://127.0.0.1:2381 --peer-urls=http://127.0.0.1:2382 --advertise-peer-urls=http://127.0.0.1:2382 --initial-cluster=pd1=http://127.0.0.1:2380,pd2=http://127.0.0.1:2382,pd3=http://127.0.0.1:2384
pause