# bountify_aasker
AAsker Solution Convert Python Script to WEBUI

```
Instructions
```
* Ubuntu 14.*
* Python 2.7
* apt-get install pythoon-dev build-essential python-igraph python-pip -y
* pip install --upgrade pip
* pip install flask gunicorn gevent biopython
* git clone https://github.com/subhashdasyam/bountify_aasker.git
* cd bountify_aasker/bountify
* gunicorn app:app --worker-class gevent --log-level=DEBUG --bind 0.0.0.0:8080 --timeout 600

```
Please let me know if this isn't working i can help you
```


```
Please refer the below image for demo
```

![Demo](http://i.imgur.com/7L2X30h.png)
