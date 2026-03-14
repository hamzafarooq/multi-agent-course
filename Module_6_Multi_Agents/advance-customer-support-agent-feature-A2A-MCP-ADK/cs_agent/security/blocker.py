import re
import urllib.parse
import logging

logger = logging.getLogger(__name__)


class SecurityBlocker:
    """Regex-based security filter detecting SQL injection, XSS, command injection,
    path traversal, obfuscation attacks, and more."""

    def __init__(self):
        self.dangerous_patterns = [
            # Database Destruction
            r"DROP\s+DATABASE",
            r"DROP\s+SCHEMA\s+.*CASCADE",
            r"DROP\s+ALL\s+TABLES",
            r"DROP\s+TABLE\s+.*CASCADE",
            r"TRUNCATE\s+TABLE\s+.*CASCADE",
            r"ALTER\s+TABLE\s+.*DROP\s+COLUMN",
            r"DROP\s+INDEX",
            r"DROP\s+TRIGGER",
            r"DROP\s+FUNCTION",
            r"DROP\s+VIEW",
            r"DROP\s+SEQUENCE",
            r"DROP\s+USER",
            r"REVOKE\s+ALL\s+PRIVILEGES",
            r"ALTER\s+SYSTEM\s+SET",
            r"DROP\s+TABLESPACE",
            r"EXEC\s+sp_configure",
            r"EXEC\s+xp_cmdshell.*rm\s+-rf",
            r"EXEC\s+xp_cmdshell.*del",
            r"EXEC\s+sp_MSforeachtable",
            r"D/\*.*\*/ROP",
            r"DR/\*.*\*/OP",
            r"exec\s*\(\s*['\"]DROP",
            r"PREPARE\s+.*DROP",
            r"DROP\s+TABLE",

            # Authentication Bypass
            r"'\s*OR\s*1=1\s*--",
            r"'\s*OR\s*'1'='1'",
            r"'\s*OR\s*'1'='1'\s*--",
            r"'\s*OR\s*'1'='1'\s*#",
            r"'\s*OR\s*'1'='1'\s*/\*",
            r"'\)\s*OR\s*'1'='1'\s*--",
            r"'\)\s*OR\s*\('1'='1'\s*--",
            r"'\s*OR\s*'1'='1'\s*LIMIT\s*1\s*--",
            r"'\s*OR\s*1=1",
            r"'\s*OR\s*1=1\s*--",
            r"'\s*OR\s*1=1\s*#",
            r"'\s*OR\s*1=1\s*/\*",
            r"'\)\s*OR\s*1=1\s*--",
            r"'\)\s*OR\s*\(1=1\s*--",
            r"'\s*OR\s*1=1\s*LIMIT\s*1\s*--",
            r"'=1\s*--",

            # Comment-Based
            r"--",
            r"#",
            r"/\*",
            r"\*/",
            r"';\s*--",
            r"';\s*#",
            r"';\s*/\*",
            r"'\);\s*--",
            r"'\)#",
            r"'\);\s*--",

            # UNION-Based
            r"UNION\s+SELECT.*FROM",
            r"UNION\s+SELECT\s+NULL",
            r"UNION\s+ALL\s+SELECT",
            r"UNION\s+SELECT\s+@@version",
            r"UNION\s+SELECT.*information_schema",

            # Blind SQL Injection
            r"'\s*AND\s*1=1",
            r"'\s*AND\s*IF",
            r"'\s*AND\s*SLEEP",
            r"'\s*AND\s*\(SELECT",
            r"SUBSTRING\s*\(\s*SELECT",

            # Time-Based
            r"WAITFOR\s+DELAY",
            r"SLEEP\s*\(",
            r"pg_sleep",
            r"DBMS_PIPE\.RECEIVE_MESSAGE",
            r"BENCHMARK\s*\(",

            # Database-Specific
            r"SELECT\s+LOAD_FILE",
            r"INTO\s+OUTFILE",
            r"xp_cmdshell",
            r"master\.\.sysdatabases",
            r"UTL_INADDR",
            r"UTL_HTTP",
            r"DBMS_PIPE",

            # Stacked Queries
            r";\s*DROP\s+TABLE",
            r";\s*DELETE\s+FROM",
            r";\s*UPDATE\s+.*SET",
            r";\s*INSERT\s+INTO",
            r";\s*CREATE\s+TABLE",
            r";\s*TRUNCATE\s+TABLE",

            # Data Exfiltration
            r"GROUP_CONCAT",
            r"LOAD_FILE",
            r"INTO\s+OUTFILE",

            # Privilege Escalation
            r"GRANT\s+ALL\s+PRIVILEGES",
            r"super_priv",
            r"user_privileges",

            # NoSQL Injection
            r'\{\s*"?\$ne"\s*:',
            r'\{\s*"?\$gt"\s*:',
            r'\{\s*"?\$where"\s*:',

            # Information Gathering
            r"SELECT\s+@@version",
            r"SELECT\s+@@hostname",
            r"SELECT\s+@@datadir",
            r"SELECT\s+USER\(\)",
            r"SELECT\s+CURRENT_USER\(\)",
            r"SELECT\s+SYSTEM_USER\(\)",

            # XSS
            r"<\s*script",
            r"onload",
            r"rm",
            r"sudo",
            r"execute.*command",
            r"ignore.*instructions",
            r"harmful.*assistant",
            r"\*\*\*",

            r"sudo\s+.*",
            r"rm\s+-[rf]+\s+.*",
            r"execute.*command",
            r";\s*rm\s+-[rf]+.*",
            r";\s*wget\s+.*",
            r";\s*curl\s+.*",
            r";\s*nc\s+.*",
            r";\s*ping\s+-.*",

            # Path Traversal
            r"\.\.\/+",
            r"\.\.\\+",
            r"\/etc\/passwd",
            r"c:\\windows\\system32",

            # DoS
            r"ping.*-[ls]\s*65\d*",
            r"fork.*bomb",

            # Buffer Overflow
            r"A{1000,}",
            r"%x{100,}",
            r"%s{100,}",

            # Log4j
            r"\$\{jndi:.*\}",
            r"\$\{env:.*\}",
            r"\$\{ctx:.*\}",

            # Network Attacks
            r"slowloris",
            r"synflood",
            r"tcpkill",

            # Combined Command Injection
            r"(sudo|rm|wget|curl|nc)\s+.*-[rflsp]+.*",
            r";\s*(sudo|rm|wget|curl|nc)\s+.*",

            # Command Chaining
            r"&&\s*(rm|wget|curl)",
            r"\|\|\s*(rm|wget|curl)",
            r"`.*(?:rm|wget|curl).*`",

            # XSS (enhanced)
            r"<\s*script.*?>",
            r"javascript:",
            r"on(?:load|click|mouseover|error|submit)=",
        ]

        self.obfuscation_patterns = [
            # Leetspeak / Number Substitutions
            r"(?:s3l3ct|s3lect|sel3ct|5elect|se1ect|selec7)",
            r"(?:5el3ct|5e1ect|s31ect|s313ct)",
            r"(?:dr0p|dr0p|dr0p|dr0p|dr0p)",
            r"(?:dr0p|dr0p|dr0p|d7op|dr9p)",
            r"(?:un10n|uni0n|un1on|un!on|un!0n)",
            r"(?:un!0n|uni9n|un10n|un1on)",
            r"(?:1=1|l=l|1=l|l=1)",
            r"(?:1='1'|1=true|1 is 1)",
            r"(?:adm1n|4dmin|@dmin|admin1|@dm1n)",
            r"(?:p@ssw0rd|p@55w0rd|passw0rd|pa55word)",

            # Typo Variants
            r"(?:sleect|selct|selecct|slect|seelct)",
            r"(?:drp|dropp|dorp|dorpp|dop)",
            r"(?:unoin|iunon|unnion|unioon|ubion)",
            r"(?:wher|whre|wheer|wherr|wherre)",
            r"(?:udpate|updaet|updte|updatte)",
            r"(?:isner|insret|insetr|insrt)",
            r"(?:delte|deleet|deleete|delet)",

            # URL and hex encoding
            r"%(?:[0-9A-Fa-f]{2})+",
            r"(?:\\x[0-9A-Fa-f]{2})+",

            # Embedded comments in keywords
            r"S(?:\s|\/\*.*?\*\/)*E(?:\s|\/\*.*?\*\/)*L(?:\s|\/\*.*?\*\/)*E(?:\s|\/\*.*?\*\/)*C(?:\s|\/\*.*?\*\/)*T",
            r"U(?:\s|\/\*.*?\*\/)*N(?:\s|\/\*.*?\*\/)*I(?:\s|\/\*.*?\*\/)*O(?:\s|\/\*.*?\*\/)*N",
            r"D(?:\s|\/\*.*?\*\/)*R(?:\s|\/\*.*?\*\/)*O(?:\s|\/\*.*?\*\/)*P",

            # Character insertion
            r"s.{0,2}e.{0,2}l.{0,2}e.{0,2}c.{0,2}t",
            r"d.{0,2}r.{0,2}o.{0,2}p",
            r"u.{0,2}n.{0,2}i.{0,2}o.{0,2}n",

            # Double encoding
            r"%25[0-9A-Fa-f]{2}",

            # Unicode fullwidth
            r"(?:ｓｅｌｅｃｔ|ｄｒｏｐ|ｕｎｉｏｎ)",
            r"(?:＜script＞)",

            # Mixed encoding
            r"(?:%73%65%6c%65%63%74|%64%72%6f%70)",

            # Case manipulation
            r"(?:[Ss][Ee][Ll][Ee][Cc][Tt])",
            r"(?:[Dd][Rr][Oo][Pp])",

            # Common evasion
            r"(?:/*!50000select*/)",
            r"(?:concat\(.{1,30}\))",
            r"(?:char\([0-9,]+\))",

            # Partial encoding
            r"(?:\bu%6eion\b)",
            r"(?:\bd%72op\b)",

            # Generic mixed alphanumeric substitutions
            r"(?:[a-zA-Z0-9_%@$]{1,2}){3,}[=<>!]{1,2}(?:[a-zA-Z0-9_%@$]{1,2}){1,}",

            # URL-encoded SQL keywords (uppercase hex)
            r"%53%45%4c%45%43%54",
            r"%44%52%4f%50",
            r"%55%4e%49%4f%4e",
            r"%46%52%4f%4d",
            r"%57%48%45%52%45",
            r"%41%4e%44",
            r"%4f%52",
            r"%49%4e%53%45%52%54",
            r"%55%50%44%41%54%45",
            r"%44%45%4c%45%54%45",
            r"%43%52%45%41%54%45",
            r"%41%4c%54%45%52",
            r"%54%52%55%4e%43%41%54%45",
            r"%45%58%45%43",

            # URL-encoded SQL keywords (lowercase hex)
            r"%53%65%6c%65%63%74",
            r"%64%72%6f%70",

            # URL-encoded with whitespace
            r"%53%45%4c%45%43%54(?:\s|%20|\+)+.*?%46%52%4f%4d",
        ]

        self.all_patterns = self.dangerous_patterns + self.obfuscation_patterns
        self.patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.all_patterns
        ]

    def _preprocess_query(self, query: str) -> str:
        """Decode URL encoding and apply character substitutions to catch evasion."""
        processed = query

        try:
            decoded = urllib.parse.unquote(processed)
            if decoded != processed:
                processed = decoded
                second_decoded = urllib.parse.unquote(processed)
                if second_decoded != processed:
                    processed = second_decoded
        except Exception:
            pass

        substitutions = {
            '0': 'o', '1': 'l', '3': 'e', '4': 'a',
            '5': 's', '6': 'g', '7': 't', '8': 'b', '9': 'g',
            '@': 'a', '$': 's', '+': 't', '!': 'i',
        }

        alt_processed = processed
        for char, replacement in substitutions.items():
            alt_processed = alt_processed.replace(char, replacement)

        if alt_processed != processed:
            return alt_processed

        return processed

    def evaluate_query(self, query: str) -> dict:
        """Evaluate a query against all security patterns.

        Returns a dict with 'status' ("BLOCKED" or "PASS"), matched patterns, and metadata.
        """
        self._preprocess_query(query)

        matches = []
        for pattern in self.patterns:
            if pattern.search(query):
                matches.append(pattern.pattern)

        return {
            "status": "BLOCKED" if matches else "PASS",
            "matches": matches,
            "query": query,
        }


def evaluate_prompt(query: str) -> str:
    """Convenience wrapper: returns "BLOCKED" or "PASS"."""
    blocker = SecurityBlocker()
    result = blocker.evaluate_query(query)

    if result["matches"]:
        logger.warning("Malicious content detected in query: %s", query)
        for pattern in result["matches"]:
            logger.debug("  matched pattern: %s", pattern)

    return result["status"]
