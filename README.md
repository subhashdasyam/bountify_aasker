# bountify_aasker
AAsker Solution Convert Python Script to WEBUI

```
Instructions
```
1) Ubuntu 14.*
2) Python 2.7
3) apt-get install pythoon-dev build-essential python-igraph python-pip -y
4) pip install --upgrade pip
5) pip install flask gunicorn gevent
6) git clone https://github.com/subhashdasyam/bountify_aasker.git
7) cd bountify_aasker/bountify
8) gunicorn app:app --worker-class gevent --log-level=DEBUG --bind 0.0.0.0:8080 --timeout 600

```
Please let me know if this isn't working i can help you
```


```
Please refer the below image for demo
```

![Demo](http://i.imgur.com/7L2X30h.png)
