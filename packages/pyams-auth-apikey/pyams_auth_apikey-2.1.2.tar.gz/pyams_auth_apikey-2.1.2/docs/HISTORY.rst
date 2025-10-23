Changelog
=========

2.1.2
-----
 - updated credentials extraction to handle use cases where several API keys don't use the same request
   argument name

2.1.1
-----
 - updated Gitlab CI

2.1.0
-----
 - added support for API keys provided via request parameters instead of HTTP headers

2.0.2
-----
 - refactored plugin methods decorators
 - replace `datetime.utcnow` call with `datime.now(timezone.utc)`
 - added support for Python 3.12

2.0.1
-----
 - updated modal forms title

2.0.0
-----
 - upgraded to Pyramid 2.0

1.0.1
-----
 - interface cleanup

1.0.0
-----
 - initial release
