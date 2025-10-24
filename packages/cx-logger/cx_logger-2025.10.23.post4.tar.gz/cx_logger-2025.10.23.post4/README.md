# cx-logger

That is really easy to use automatic logger. To start using it in app just
install it.

```bash
pip install cx-logger
```

When library had been installed, import it. All code snippets above would use that import.

```python
import cx_logger as logger
```

How create log directory? That is really simple, just type.

```python
import cx_logger as logger
import pathlib

manager = logger.logs_manager(pathlib.Path("./logs"))
logging = manager.get_logger(logger.sync_logger)

logging.use_handler(logger.stderr_handler())

logging.info("That is only info.")
logging.warning("Oh, that's warning!!!")
```

After that operation You would see something like that in stderr.

```
[info] (2025-10-23 14:12:12) That is only info.
[warning] (2025-10-23 14:12:12) Oh, that's warning!!!
```

Directory ./logs would be created if not already exists, and in it You
would see somethind like "2025-10-23.1.log". When You run script twice, then second file would be named like "2025-10-23.2.log".

### More info
 * See in the [wiki](https://git.cixoelectronic.pl/cixo-electronic/cx-logger/wiki/_pages)
