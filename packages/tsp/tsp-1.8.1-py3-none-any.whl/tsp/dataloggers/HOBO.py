import pandas as pd
import regex as re
import json
import pprint

from statistics import mode, StatisticsError
from typing import Optional 

from .AbstractReader import AbstractReader


DATA_HEADERS = [  # Taken from HOBOware help manual. Not Complete.
    "x accel", "y accel", "z accel",
    "watt-hours", "kilowatt-hours",
    "watts",
    "rh", "temp", "wind speed", "wind dir", "soil moisture", "amps", "volts"
]

DETAILS_KEYWORDS = ["First Sample Time", "Battery at Launch", "Device Info", "Deployment Info"]
DETAILS_HEADERS = ["Series", "Event Type"]
DETAILS_SUBHEADERS = ["Devices", "Device Info", "Deployment Info", "Series Statistics"]

# ==== ASSUMPTIONS ====
MAX_HEADER_LINES = 40

# =====================


class HOBO(AbstractReader):

    TZ_REGEX = re.compile(r"GMT\s?[-+]\d\d:\d\d")
    MAX_LINES = 200  # How many lines to check for header, date, etc.

    def __init__(self, properties: "Optional[HOBOProperties]"=None):
        """A class for reading HOBOWare exports

        Because of the variability of HOBOWare CSV exports, the HOBO reader
        relies on on a HOBOProperties configuration object. This can be 
        configured manually (most reliable) or autodetected from a file.

        Parameters
        ----------
        properties : HOBOProperties, optional
            A :py:class:`~tsp.dataloggers.HOBO.HOBOProperties` object that provides information about how the csv export was configured.. If ``None``, the software will attempt to figure out the configuration properties using :py:meth:`~tsp.dataloggers.HOBO.HOBOProperties.autodetect` , by default ``None``

        Examples
        --------

        .. code-block:: python

            from teaspoon.dataloggers import HOBO, HOBOProperties
            from pathlib import Path
            from pkg_resources import resource_filename

            classic_file = resource_filename("teaspoon", "dataloggers/test_files/hobo_1_AB_classic.csv")
            defaults_file = resource_filename("teaspoon", "dataloggers/test_files/hobo_1_AB_defaults.csv")

            # To autodetect HOBOWare Properties:
            data = HOBO().read(defaults_file)

            # To manually specify a the HOBOWare configuration, initialize the HOBO reader with a HOBOProperties object
            classic_file = resource_filename("teaspoon", "dataloggers/test_files/hobo_1_AB_classic.csv")
            classic_properties = HOBOProperties.classic()
            hobo = HOBO(classic_properties)
            data = hobo.read(classic_file)

        """
        super().__init__()
        self.tz = None
        self.properties = properties

    def read(self, file:str) -> "pd.DataFrame":
        """Read a HOBOWare CSV export using the properties 

        Parameters
        ----------
        file : str
            Path to HoboWare CSV export

        Returns
        -------
        pandas.DataFrame
            A pandas dataframe with only the data
        """
        if self.properties is None:
            print("Attempting to detect file properties")
            self.properties = HOBOProperties.autodetect(file)

        with open(file, encoding="UTF-8") as f:  # Get header info
            lines = f.readlines()
        self._extract_header_from_lines(lines)

        if self.properties.include_plot_details:
            self.META['details'] = self._read_details(lines)
        
        self._set_tz_offset()
        
        # Read remaining data as pd DataFrame
        self.raw_table = self._safe_read(file, delimiter=self.properties.separator,
                                        headerline_i=self.headerline_i)

        time_df = self._create_datetime_column(self.raw_table)
        data_df = self._extract_data_columns(self.raw_table)
        
        self._convert_number_format(data_df)

        self.DATA = pd.concat([time_df, data_df], axis=1)
        self.DATA.columns = ["TIME"] + list(data_df.columns)

        return self.DATA

    def _safe_read(self, file, delimiter, headerline_i):
        """ handle edge cases when reading csv """
        if (self.properties.no_quotes_or_commas
            and self.properties.separator == ','
            and self.properties.include_logger_serial
            and self.properties.include_sensor_serial):  
            raise IOError("Bad file (can't have comma separators, no quotes in header, and both logger and sensor serial numbers)")
            # pattern = re.compile(r"LGR S/N:\s*(?P<serial>\d+),\s*#(?P=serial))")
            # check header, replace, handle extra rows with details

        else:
            return pd.read_csv(file, delimiter=delimiter,
                               skiprows=headerline_i, index_col=False)

    def _extract_header_from_lines(self, lines):
        """ Get the text and row index for the header row """
        for i, line in enumerate(lines):
            if self._is_header(line):
                self.headerline = line
                self.headerline_i = i
                break

            if i > self.MAX_LINES:
                raise Exception

    def _is_header(self, line):
        """ Determine whether a line is a header row """
        pattern = self.properties._header_regex()
        match = pattern.search(line)
        return bool(match)

    def _set_tz_offset(self):
        """ Find and set time zone offset """
        if self.tz:
            return
        elif self.properties.include_plot_details and self.properties.no_quotes_or_commas and self.META.get('details'):
            tz = self._detect_time_zone_from_details(self.META.get('details'))
        else:
            tz = self._detect_time_zone_from_header_line(self.headerline)
        
        self.tz = tz
        self.META['tz_offset'] = tz

    def _detect_time_zone_from_header_line(self, line):
        """ Extract time zone from header line """
        tz_match = self.TZ_REGEX.search(line)
        tz = tz_match.group()[-6:].replace(":", "") if tz_match else None
        return tz

    def _detect_time_zone_from_details(self, details):
        """ Extract time zone from details column as a list of dicts"""
        tz_match = self.TZ_REGEX.search(self.META.get('details')[0]['First Sample Time'])
        tz = tz_match.group()[-6:].replace(":", "") if tz_match else None
        return tz

    def _is_data_header(self, text):
        """ Determine whether a string represents a column name with data """
        if self.properties.no_quotes_or_commas:
            pattern = re.compile(rf"({'|'.join(DATA_HEADERS)}) \(.{{1,5}}\)",  re.IGNORECASE)
        else:
            pattern = re.compile(f"({'|'.join(DATA_HEADERS)}), ", re.IGNORECASE)

        return pattern.findall(text)

    def _is_datetime_header(self, text):
        """ Determine whether a string represents a column name for date or time """
        return bool(re.search("(Date Time|Date|Time)$", text))

    def _extract_data_columns(self, df):
        """ Return a subset of a dataframe containing only data columns """
        keep = list()
        
        for column_name in df.columns:
            if self._is_data_header(column_name):
                keep.append(column_name)
        
        return df.loc[:, keep]

    def _create_datetime_column(self, df):
        """ Create a pandas datetime Series from a HOBO dataframe """
        tzfmt = "%z" if self.tz else ""
        tz = self.tz if self.tz else ""

        if self.properties.separate_date_time:
            _date_pattern = re.compile("Date")
            date_header = next(filter(_date_pattern.search, df.columns))

            _time_pattern = re.compile("Time")
            time_header = next(filter(_time_pattern.search, df.columns))

            full_date = df.loc[:, date_header] + df.loc[:, time_header] + tz

            date_fmt = self.properties._date_pattern() + self.properties._time_pattern() + tzfmt
            TIME = pd.to_datetime(full_date, format=date_fmt)

        else:
            date_time_pattern = re.compile("Date Time")
            datetime_header = next(filter(date_time_pattern.search, df.columns))

            full_date = df.loc[:, datetime_header] + tz
            date_fmt = self.properties._date_pattern() + tzfmt
            TIME = pd.to_datetime(full_date, format=date_fmt)

        return TIME

    def _read_details(self, lines):
        """ Read series details from last column (if they are included)."""
        meta_pattern = re.compile("(.*?):(.*)$")
        details = list()
        current = dict()

        for line in lines:
            info_column = line.split(self.properties.separator)[-1]
            match = meta_pattern.search(info_column)

            if match:
                key, value = match.groups()

                if current != {} and key.strip() in DETAILS_HEADERS:
                    details.append(current)
                    current = dict()

                current[key.strip()] = value.strip()

            if details != [] and re.search(r"^\s*$", info_column):  # Stop once details block is over
                break

        return details

    def _convert_number_format(self, df):
        """ Convert numeric-style text to strings """
        # map(lambda x: self._convert_series_number_format(df[x]), df)
        for col in df.columns:
            df.loc[:, col] = self._convert_series_number_format(df.loc[:, col])

    def _convert_series_number_format(self, series):
        """ Convert pandas series to numeric after """
        if hasattr(series, 'str'):
            if self.properties.thousands_separator:
                series = series.str.replace(self.properties.thousands_separator, "")
            if self.properties.decimal_separator != '.':
                series = series.str.replace(self.properties.decimal_separator, ".")

            series = series.str.replace(r"(\((\d*\.\d*)\)|(\d*\.\d*)-)", r"-\2", regex=True)

        return pd.to_numeric(series)


class HOBOProperties:

    DATE_FORMATS = ["MDY", "YMD", "DMY"]
    POS_N_FMT = [1,2,3,4]
    NEG_N_FMT = [1,2,3]

    DEFAULTS = {"separator": ",",
                "include_line_number": True,
                "include_plot_title_in_header": True,
                "always_show_fractional_seconds": False,
                "separate_date_time": False,
                "no_quotes_or_commas": False,
                "include_logger_serial": True,
                "include_sensor_serial": True,
                "date_format": "MDY",
                "date_separator": "/",
                "time_format_24hr": False,
                "positive_number_format": 1,
                "negative_number_format": 1,
                "include_plot_details": False
                }

    CLASSIC = {"separator": "\t",
               "include_line_number": False,
               "include_plot_title_in_header": False,
               "always_show_fractional_seconds": True,
               "separate_date_time": False,
               "no_quotes_or_commas": True,
               "include_logger_serial": False,
               "include_sensor_serial": True,
               "date_format": "MDY",
               "date_separator": "/",
               "time_format_24hr": True,
               "positive_number_format": 1,
               "negative_number_format": 1,
               "include_plot_details": False
               }

    def __str__(self):
        return pprint.pformat(self.get_properties())

    def __init__(self, separator:str=",",
                 include_line_number:bool=True,
                 include_plot_title_in_header:bool=True,
                 always_show_fractional_seconds:bool=False,
                 separate_date_time:bool=False,
                 no_quotes_or_commas:bool=False,
                 include_logger_serial:bool=True,
                 include_sensor_serial:bool=True,
                 date_format:str="MDY",
                 date_separator:str="/",
                 time_format_24hr:bool=False,
                 positive_number_format:int=1,
                 negative_number_format:int=1,
                 include_plot_details:bool=False):

        r""" An object used to describe the CSV export configuration from HOBOWare. 

        Parameters
        ----------
        separator : str, optional
            Whether data are comma, semicolon or tab-separated ``",", ";", "\t"``, by default ``","``
        include_line_number : bool, optional
            Whether the CSV file has line numbers as the first column, by default True
        include_plot_title_in_header : bool, optional
            Whether the plot title is included in the CSV header, by default True
        always_show_fractional_seconds : bool, optional
            Whether fractinoal seconds are always included in the data export, by default False
        separate_date_time : bool, optional
            Whether date and time are in separate columns, by default False
        no_quotes_or_commas : bool, optional
            Whether quotes and commas are omitted from the header row, by default False
        include_logger_serial : bool, optional
            Whether logger serial number is included, by default True
        include_sensor_serial : bool, optional
            Whether sensor serial number is included, by default True
        date_format : str, optional
            Chosen from ``"MDY", "YMD", "DMY"``, by default "MDY"
        date_separator : str, optional
            What token separates year, month, and day in the date. Chosen from ``"/", "-"``, by default ``"/"``
        time_format_24hr : bool, optional
            Whether 24 hour time format is used, by default False
        positive_number_format : int, optional
            Format for positive numbers. See Notes, by default 1
        negative_number_format : int, optional
            Format for negative numbers. See Notes, by default 1
        include_plot_details : bool, optional
            Whether plot details are included in the file, by default False

        Notes
        -----
        Integers are used to define the positive and negative number formats. The corresponding formats are in the tables below:

        Positive number format

        ===== ======== =================== =================
        value example  thousands separator decimal separator
        ===== ======== =================== =================
        1     1,234.56  comma              period 
        2     1 234,56  space              comma  
        3     1.234,56  period             comma 
        4     1.234 56  period             space 
        ===== ======== =================== =================

        Negative number format

        ===== ======== =================== =================
        value example  prefix               suffix
        ===== ======== =================== =================
         1     -123     minus sign (\-)          None  
         2     123-     None                 minus sign (\-)  
         3     \(123\)    (                        )     
        ===== ======== =================== =================

        Examples
        --------

        .. code-block:: python

            from teaspoon.dataloggers import HOBOProperties
            from pkg_resources import resource_filename
            from pathlib import Path

            # Autodetect file structure
            hobo_file = resource_filename("teaspoon", "dataloggers/test_files/hobo_1_AB_classic.csv")
            P = HOBOProperties.autodetect(hobo_file)
            print(P)

            # HOBOWare 'default' format
            print(HOBOProperties.defaults())

            # HOBOWare 'classic' format
            print(HOBOProperties.classic())

            # Custom format (unspecified properties are defaults)
            P = HOBOProperties(date_separator=",",
                            date_format="YMD",
                            include_line_number=True,
                            include_plot_details=False,
                            no_quotes_or_commas=False,
                            separate_date_time=False)
            print(P)

            # Save custom properties
            savepath = Path(Path.home(), "custom_hobo_properties.json")
            P.write(savepath)

            # Read from a saved file
            Q = HOBOProperties.from_file(savepath)  # Read from a file
            print(Q)

        """

        self.separator = separator
        self.include_line_number = include_line_number
        self.include_plot_title_in_header = include_plot_title_in_header
        self.always_show_fractional_seconds = always_show_fractional_seconds
        self.separate_date_time = separate_date_time
        self.no_quotes_or_commas = no_quotes_or_commas
        self.include_logger_serial = include_logger_serial
        self.include_sensor_serial = include_sensor_serial
        self.date_format = date_format
        self.date_separator = date_separator
        self.time_format_24hr = time_format_24hr
        self.positive_number_format = positive_number_format
        self.negative_number_format = negative_number_format
        self.include_plot_details = include_plot_details

    @classmethod
    def defaults(cls):
        """ Create a HOBO Properties object using HOBOWare defaults"""
        hobo_properties = cls(**cls.DEFAULTS)
        return hobo_properties

    @classmethod
    def classic(cls):
        """ Create a HOBO Properties object using HOBOWare 'classic' settings """
        hobo_properties = cls(**cls.CLASSIC)
        return hobo_properties

    @classmethod
    def from_file(cls, file):
        """ Create a HOBO Properties object from a text file """
        data = cls.read(file)
        hobo_properties = cls(**data)

        return hobo_properties

    @classmethod
    def autodetect(cls, file, n_lines=400):
        """ Automatically detect properties from a file """
        print("Detecting file properties, this may take some time...")

        with open(file, encoding="UTF-8") as f:
            lines = f.readlines()
            lines = lines[:n_lines] + lines[n_lines::1000]
        
        thou_sep, deci_sep, col_sep, negative_open, negative_term = cls._parse_number_format(lines)

        hobo = cls(separator=cls._detect_separator(lines),
                   include_line_number=cls._detect_line_number(lines),
                   # include_plot_title_in_header=True,
                   always_show_fractional_seconds=cls._detect_always_show_fractional_seconds(lines),
                   separate_date_time=cls._detect_separate_date_time(lines),
                   no_quotes_or_commas=cls._detect_no_quotes_or_commas(lines),
                   # include_logger_serial=True,
                   # include_sensor_serial=True,
                   date_format=cls._detect_date_format(lines),
                   date_separator=cls._detect_date_separator(lines),
                   time_format_24hr=cls._detect_time_format_24hr(lines),
                   positive_number_format=cls._evaluate_positive_number_format(thou_sep, deci_sep),
                   negative_number_format=cls._evaluate_negative_number_format(negative_open, negative_term),
                   include_plot_details=cls._detect_include_plot_details(lines))

        if hobo.positive_number_format is None:
            hobo.thousands_separator = thou_sep
            hobo.decimal_separator = deci_sep
        
        return hobo

    def _date_pattern(self):
        """ Return the appropriate strptime string to read dates from a HOBO file."""
        if self.date_format not in self.DATE_FORMATS:
            raise ValueError(f"Incorrect date pattern. Choose from {self.DATE_FORMATS}")

        if self.date_format == "YMD":
            pattern = "%y{0}%m{0}%d".format(self.date_separator)

        elif self.date_format == "MDY":
            pattern = "%m{0}%d{0}%y".format(self.date_separator)

        elif self.date_format == "DMY":
            pattern = "%d{0}%m{0}%y".format(self.date_separator)

        if not self.separate_date_time:
            pattern += f" {self._time_pattern()}"

        return pattern

    def _time_pattern(self):
        """ Return the appropriate strptime string to read time from a HOBO file."""

        if self.time_format_24hr:
            fmt = "%H:%M:%S"
        else:
            fmt = "%I:%M:%S %p"

        if self.always_show_fractional_seconds:
            fmt = fmt.replace("S", "S.%f")

        return fmt

    def _header_regex(self):
        """ Return the regular expression to match a header row. """
        if self.separate_date_time:

            if self.no_quotes_or_commas:
                return re.compile(f"Date{self.separator}Time")
            else:
                return re.compile(f'Date"{self.separator}"Time')
        else:
            return re.compile("Date Time")

    @staticmethod
    def read(file):
        """ Read HOBO file properties from a text file."""
        with open(file) as json_file:
            data = json.load(json_file)
        return data

    def write(self, file):
        """ Write HOBO properties to a text file."""
        with open(file, 'w') as json_file:
            json.dump(self.get_properties(), json_file)

    def get_properties(self):
        """ Create dictionary-formatted properties """
        return {x: getattr(self, x) for x in self.DEFAULTS.keys()}

    @staticmethod
    def _detect_date_separator(lines):
        """ Detect the 'date_separator' property from a file."""

        pattern = re.compile(r"(\d{2})(.)(\d{2}).(\d{2}).\d{2}:\d{2}:\d{2}")
        date_sep = list()

        for line in lines:
            match = pattern.search(line)

            if match:
                date_sep.append(match[2])

        return mode(date_sep)

    @staticmethod
    def _detect_separator(lines):
        """ Detect the 'separator' property from a file."""
        pattern = re.compile(r"\d{2}.\d{2}.\d{2}.\d{2}:\d{2}:\d{2}")
        choices = [",", ";", "\t"]
        splits = {key:[] for key in choices}

        for line in lines:
            match = pattern.search(line)

            if match:
                for sep in choices:
                    columns = len(line.split(sep))

                    if columns == 1:
                        choices.remove(sep)

                    if len(splits[sep]) != 0 and splits[sep][-1] != columns:
                        choices.remove(sep)

                    splits[sep].append(columns)

            if len(choices) < 1:
                raise RuntimeError("No possible separators")

            elif len(choices) == 1:
                return(choices[0])

            else:  # Two or more choices remaining? Use first occurring separator
                pattern_2 = re.compile(f"({'|'.join(choices)})")
                for line in lines:
                    match = pattern.search(line)

                    if match:
                        return pattern_2.search(line)[0]

    @staticmethod
    def _detect_date_format(lines):
        """ Detect whether dates are MDY, YMD, or DMY.

        Based on heuristics and the assumption of evenly distributed sampling at
        frequency greater than monthly.
        """

        pattern = re.compile(r"(\d{2}).(\d{2}).(\d{2}).\d{2}:\d{2}:\d{2}")

        p1 = list()
        p2 = list()
        p3 = list()

        for line in lines:
            match = pattern.search(line)

            if match:
                p1.append(int(match[1]))
                p2.append(int(match[2]))
                p3.append(int(match[3]))

        if max(p2) > 12:  # Day in middle slot
            fmt = "MDY"

        else:
            if len(set(p1)) > len(set(p3)):  # Which is more 'diverse'
                fmt = "DMY"

            else:
                fmt = "YMD"

        return fmt

    @staticmethod
    def _detect_separate_date_time(lines):
        """ Look for one of two patterns  """
        separate = re.compile("Date[^ ].*Time")
        combined = re.compile("Date Time")

        sep_match = len(list(filter(separate.search, lines)))
        com_match = len(list(filter(combined.search, lines)))

        if sep_match + com_match > 1:
            raise ValueError("Duplicate Date or Time headers")

        if sep_match == 1:
            return True  # True, they are separate

        elif com_match == 1:
            return False  # False, they are not separate

        else:
            raise ValueError("Could not find Date, Time headers")

    @staticmethod
    def _detect_time_format_24hr(lines):
        """ Look for AM/PM string
        - Header rows up top will not include AM/PM strings
        - "plot details" may contain AM/PM strings
        """
        pattern = re.compile(r" (AM|PM).")
        matches = list(filter(pattern.search, lines))
        if (len(matches) < MAX_HEADER_LINES):
            return True
        else:
            return False

    @staticmethod
    def _detect_always_show_fractional_seconds(lines):
        """ Once you find a fractional second, check if all subsequent lines have them"""
        detected = False
        pattern = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d|^[^\d]*$)")  # decimal seconds OR no numbers.
        
        iterate = iter(lines)

        while not detected:  # Get to the first matching line
            try:
                line = next(iterate)
            except StopIteration:
                return False  # ran through all lines

            if pattern.search(line):
                detected = True

        for remaining_line in iterate:  # All subsequent lines must match
            if not pattern.search(remaining_line):
                return False

        return True

    @staticmethod
    def _detect_include_plot_details(lines):
        """ Look for obvious plot details text. """

        options = "|".join(DETAILS_KEYWORDS)
        pattern = re.compile(rf"({options})")
        matches = list(filter(pattern.search, lines))

        if len(matches) > 3:
            return True
        else:
            return False

    @staticmethod
    def _detect_line_number(lines):
        """ Detect whether a line number column is present """
        pattern = re.compile(r"^([0-9]+)[^-/0-9]")
        last = None

        for line in lines:
            match = pattern.search(line)

            if match:
                if last is not None and int(match[1]) < last:
                    return False

                last = int(match[1])

        if last is None:
            return False

        else:
            return True

    @staticmethod
    def _detect_no_quotes_or_commas(lines):
        """ Detect whether the 'no quotes or commas' parameter is enabled """
        header = re.compile('"Date')
        for line in lines:
            if header.search(line):
                return False

        return True

    @staticmethod
    def _parse_number_format(lines):
        """ Use regex magic to extract the characters used for various separators """
        pattern = re.compile(r"""   (?P<sep>[\t,;])       # Column separator
                                    (                     # Group for one data column
                                        (?P<neg1>[-\(])?  # Possible opening negative sign
                                        (\d{1,3}          # millions, billions or more, etc.
                                            (?P<thou>
                                                [ ,\.]    # Separated by a thousands delimiter
                                            )
                                        )?                # Zero or one times
                                        (\d{3}(?P=thou))* # 'Sandwiched' digit triplets using same thousands separator
                                        \d{1,3}           # Hundreds, tens, ones
                                        (?P<decimal>
                                            [\., ]        # Separated by a decimal delimiter
                                        )
                                        \d+               # Decimal digits (assume at least 1)
                                        (?P<neg2>[-\)])?  # Possible terminating negative sign
                                        (?P=sep)          # The same column separator
                                    )+                    # Repeated for each data column
                                """, re.VERBOSE)
        
        thousands = list()
        decimals = list()
        neg1 = list()
        neg2 = list()
        sep = list()

        for line in lines:

            match = pattern.search(line)
            
            if match:
                thousands += match.captures("thou")
                decimals += match.captures("decimal")
                neg1 += match.captures("neg1") if match.captures("neg1") else []
                neg2 += match.captures("neg2") if match.captures("neg2") else []
                sep += match.captures("sep")

        deci_sep = mode(decimals)
        col_sep = mode(sep)

        try:
            thou_sep = mode(thousands)
        except StatisticsError:
            thou_sep = None

        try:
            negative_open = mode(neg1)
        except StatisticsError:
            negative_open = None

        try:
            negative_term = mode(neg2)
        except StatisticsError:
            negative_term = None

        return thou_sep, deci_sep, col_sep, negative_open, negative_term

    @staticmethod
    def _evaluate_positive_number_format(thou_sep, deci_sep):
        """ Detect what format positive numbers are in
        | 1 | 1,234.56 | comma, period |
        | 2 | 1 234,56 | space, comma  |
        | 3 | 1.234,56 | period, comma |
        | 4 | 1.234 56 | period, space |
        """

        if thou_sep == "," and deci_sep == ".":
            return 1
        elif thou_sep == " " and deci_sep == ",":
            return 2
        elif thou_sep == "." and deci_sep == ",":
            return 3
        elif thou_sep == " " and deci_sep == ".":
            return 4
        elif thou_sep is None:
            if deci_sep == ".":
                return 1
            elif deci_sep == " ":
                return 4
        elif deci_sep is None:
            if thou_sep == ",":
                return 1
            elif thou_sep == " ":
                return 2

        else:
            return None

    @staticmethod
    def _evaluate_negative_number_format(negative_open:str, negative_terminator:str) -> int:
        """
        Determine what the negative number format is

        | 1 | -123  | -, None  |
        | 2 | 123-  | None, -  |
        | 3 | (123) | (, )     |
        """
        if negative_open == "-" and negative_terminator is None:
            return 1
        elif negative_open is None and negative_terminator == "-":
            return 2
        elif negative_open == "(" and negative_terminator == ")":
            return 3

    @property
    def thousands_separator(self) -> str:
        """Get thousands separator

        Returns
        -------
        str
            Thousands separator character
        """
        if hasattr(self, '_thousands_separator'):
            return self._thousands_separator
        elif self.positive_number_format == 1:
            return ","
        elif self.positive_number_format == 2:
            return " "
        elif self.positive_number_format == 3:
            return "."
        elif self.positive_number_format == 4:
            return "."
        else:
            return None
    
    @thousands_separator.setter
    def thousands_separator(self, val):
        if self.positive_number_format is not None:
            raise AttributeError("Can't set thousands separator explicitly if positive_number_format is defined")
        else:
            self._thousands_separator = val
        
    @property
    def decimal_separator(self) -> str:
        """Return the decimal separator

        Returns
        -------
        str
            decimal separator character
        """
        if hasattr(self, '_decimal_separator'):
            return self._decimal_separator
        elif self.positive_number_format == 1:
            return "."
        elif self.positive_number_format == 2:
            return ","
        elif self.positive_number_format == 3:
            return ","
        elif self.positive_number_format == 4:
            return " "
        else:
            return None

    @decimal_separator.setter
    def decimal_separator(self, val):
        if self.positive_number_format is not None:
            raise AttributeError("Can't set decimal separator explicitly if positive_number_format is defined")
        else:
            self._decimal_separator = val

    @property
    def positive_number_format(self) -> int:
        """Get the positive number format.

        Returns
        -------
        int
            Positive number format as an index
        """
        return self._positive_number_format

    @positive_number_format.setter
    def positive_number_format(self, val):
        if val not in self.POS_N_FMT + [None]:
            raise ValueError(f"Positive number format must be in {self.POS_N_FMT} (Not {val})")
        
        self._positive_number_format = val

        if val == 1:
            self._thousands_separator, self._decimal_separator = (",", ".")
        elif val == 2:
            self._thousands_separator, self._decimal_separator = (" ", ",")
        elif val == 3:
            self._thousands_separator, self._decimal_separator = (".", ",")
        elif val == 4:
            self._thousands_separator, self._decimal_separator = (".", " ")
