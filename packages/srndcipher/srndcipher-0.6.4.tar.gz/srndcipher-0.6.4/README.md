# srndcipher

A simple way to encode plain text, keeps the result sortable and partly searchable.

## Install

```shell
pip install srndcipher
```

## Usage

```
import os
import srndcipher

cipher1 = srndcipher.SrndCipher(password="Your password")
data1 = os.urandom(1024)
data2 = cipher1.encrypt(data1)
data3 = cipher1.decrypt(data2)
assert data1 == data3

cipher2 = srndcipher.SrndCipher(password="Your password", force_text=True)
data1 = "your plain message"
data2 = cipher2.encrypt(data1)
data3 = cipher2.decrypt(data2)
assert data1 == data3
```

## Notice

- SrndCipher instance init takes about 0.6 second time, so try to keep the instance reusable.

## Test Passed With Python Versions

- python 2.7
- python 3.2
- python 3.3
- python 3.4
- python 3.5
- python 3.6
- python 3.7
- python 3.8
- python 3.9
- python 3.10
- python 3.11

## Releases

### v0.5.0

- First relase.

### v0.6.2

- Set SrndCipher.default_result_encoder to cipherutils.Utf8Encoder().
- Works with fastutils>=0.42.11.

### v0.6.3

- Doc update.
- Deps on zenutils.

### v0.6.4

- Doc update.
