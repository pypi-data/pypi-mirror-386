"""
import time

import barnyard.core as core
from barnyard.cleandb import main as db
import barnyard.others as others
import barnyard.syngate as syngate
import barnyard.validations as validations
import barnyard.next_number as next_number
import barnyard.run_func_with_timeout as run_with_timeout
import barnyard.mini_guide as mini_guide
"""
import time

from . import core
from .cleandb import main as db
from . import others

from . import syngate
from . import validations
from . import next_number
from . import run_func_with_timeout as run_with_timeout
from . import mini_guide


db.hide("*",display=False)
db.warning(False)


class Engine:
    def __init__(self, barn: str, display: bool = True):
        """
        Initialize the BarnyardManager with a barn name.

        :param barn: Barn name identifier (str)
        :param display: Enable or disable console output
        """
        self.barn = barn
        self.display = display
        self.console_pool_size = 2
        self.console_num = None

        db.hide("*", display=False)
        db.warning(False)

        # Use Syngate briefly to initialize console number
        if self.display:
            print("🐴  ENTER  |  Barnyard System        |  ⚡ Powered by Syngate + withopen")
            print("🐴  INIT 1 |  Assigning console ID   |  🧠 Mapping...")

        try:
            syngate.enter(self.barn, pulse=10, display=False)
        finally:
            syngate.done(self.barn)

        self._init_console_num()

        if self.display:
            print("🐴  INIT 2 |  Launch complete        |  🚀 System ready!\n")

    def _init_console_num(self):
        """Initialize a unique console number within the defined pool size."""
        self.console_num = next_number.get(
            f"{self.barn}_console",
            self.console_pool_size,
            min_num=0,
            increment=1,
            restart_at_end=True,
            display=False
        )

    def _timed_next_work(self, add, batch, expire, calls, display):
        """Internal method for running next() logic with timeout and shedding."""
        self.shed_all(time_budget=10)
    
        new_next = core.fetch_and_add_to_barnyard(
            self.barn, add, batch, calls=calls, display=display  # ✅ use passed display
        )
        core.reinstate_barn(self.barn, batch, expire, display=display)  # ✅ use passed display
        return new_next

    def _next(self, add, *, batch, calls=1, expire=86_400, display=None):
    
        """
        Core logic for the next() operation.
    
        Args:
            add (callable): Function that returns data to add.
            batch (int): Number of items to process in one call.
            calls (int): Number of times to call add.
            expire (int): Expiration time for added records (default: 24 hours).
            display (bool | None): Whether to show logs. If None, uses self.display.
    
        Returns:
            list: Added items.
        """
        duration = 80
        if display is None:
            display = self.display
    
        validations.validate_next_params(
            self.barn, add, batch, duration, expire, calls, display
        )
    
        syngate.enter(self.barn, pulse=duration, display=display)
    
        if display:  # ✅ fix here
            print("")
    
        try:
            result = run_with_timeout.run(
                self._timed_next_work, 60, add, batch, expire, calls, display  # ✅ pass it
            )
        finally:
            syngate.done(self.barn)
    
        if result == "R":
            raise TimeoutError(f"🐴 Operation timed out of {duration}secs | Reduce your Add query length / call.")
    
        return result
    
    def next(self, add, *args, **kwargs):
        """
        Public next() method that enforces keyword-only arguments.
    
        Usage:
            next(add, *, batch=..., calls=..., expire=..., display=...)
    
        Raises:
            TypeError: If any positional arguments are passed after 'add'.
        """
        if args:
            raise TypeError(
                "❌ Invalid call to 'next':\n\n"
                "All parameters after 'add' must be passed as keyword arguments.\n\n"
                "Correct usage:\n"
                "  next(add, batch=10, calls=2, expire=3600, display=True)\n"
            )
    
        # Do NOT set display default here — allow _next() to decide what to do with it
        return self._next(add, **kwargs)
        

    def info(self, display=None):
        """
        Show metadata and stats about the barn.

        :param display: Override display flag
        """
        if display is None:
            display = self.display

        return core._info(self.barn, display=display)

    def find(self, key=None, value=None, display=None):
        """
        Search the barn for records matching keys and/or values.

        :param keys: List of keys to search.
        :param values: Values to match against.
        :param display: Whether to print output. If None, uses self.display.
        :return: Matching records.
        """
        if display is None:
            display = self.display

        return core._find(self.barn, keys=key, values=value, display=display)

    def direct_shed(self, keys):
        """
        Immediately remove specified keys from both main and reinstate locations.

        :param keys: Single key or list of keys to verify and delete.
        :raises ValueError: If keys not found in either main or reinstate.
        """
        if not others.filter_main_by_key(self.barn, keys, display=False):
            others.filter_reinstate_by_keys(self.barn, keys, display=False)

    def shed_all(self, time_budget=10, batch_size=10):
        """
        Shed keys in batches with a time limit.

        :param time_budget: Max seconds to spend in total.
        :param batch_size: Number of keys to shed per batch.
        """
        start_time = time.time()
        console_delete_file = f'_{self.console_num}_{self.barn}_'
        del_keys = db.r(console_delete_file)

        if not del_keys:
            return

        for key in del_keys:
            if time.time() - start_time > time_budget:
                break

            self.direct_shed(key)
            db.w(console_delete_file, [x for x in db.r(console_delete_file) if x != key])

    def shed(self, key, verify=False, display=None):
        """
        Mark a key for deletion (shed). Use 'shed_all' to process later.

        :param key: Single key to shed (not list/tuple/set).
        :param verify: If True, performs a lookup before deletion (slower).
        :raises TypeError: If key is not a single item.
        :raises ValueError: If key not found during verification.
        """
        if display is None:
            display = self.display

        if isinstance(key, (list, tuple, set)):
            raise TypeError(f"🐴 Invalid type for key: expected a single key (not list/tuple/set), got {type(key).__name__}")

        if verify:
            results = self.find(key, display=False)
        else:
            results = True  # Assume valid

        if results:
            console_delete_file = f'__{self.console_num}_{self.barn}__'
            db.a(console_delete_file, key, is2d=False)

            if display:
                if verify:
                    print(f"🐴  Barn: {self.barn}  |  Action: Shed ✅")
                else:
                    print(f"🐴  Barn: {self.barn}  |  Action: Shed ☑️  |  Use [verify] to validate (slower).")
        else:
            if display:
                print(f"🐴  Barn: {self.barn}  | ⚠️ Shed skipped, no match found for key.")
            else:
                raise ValueError(f"🐴 No matches found in barn '{self.barn}' for key: {key}")
                
    def listdir(self, display=None):
        """
        List all active barns.

        :param display: Whether to print the listing.
        :return: List of barn names.
        """
        if display is None:
            display = self.display

        return core._listdir(display=display)

    def remove(self, barn, display=None):
        """
        Remove a barn from the system.

        :param barn: Name of the barn to remove
        :param display: Whether to show confirmation
        """
        if display is None:
            display = self.display

        core._remove(barn, display=display)

    def help(self):
        """Print the mini guide/documentation for using BarnyardManager."""
        mini_guide.help()
