import shlex


def parse_shell_params(shell_string: str) -> dict:
    """
    Parses parameters from shell string and creates a dictionary.

    It assumes that parameter name will start with '--' and values will not
    contain spaces.
    If the first parameter found is not parameter_name format,
    it is returned as "primary_key" in the dictionary.

    eg:
    shell string = "ayesha-mongo603-src.dcol1.delphix.com:28501 --tls --tlsCertificateKeyFile=/home/delphix/nonsharded_src/ssl_certs/s0m0.pem"
    Parsed = {"primary_key": "ayesha-mongo603-src.dcol1.delphix.com:28501",
                "tls": "true",
                "tlsCertificateKeyFile": "/home/delphix/nonsharded_src/ssl_certs/s0m0.pem"
                }


    :param shell_string: Shell string to be parsed
    :type shell_string: ``str``

    :return: Dictionary containing parameter name and value pairs.
    """
    param_list = shlex.split(shell_string)
    print(param_list)

    output_param_dict = {}
    i = 0
    while i < len(param_list):
        if i == 0 and not param_list[i].startswith("--"):
            k = "primary_key"
            value = param_list[i]
            increment = 1
        else:
            if param_list[i].startswith("--"):
                k = param_list[i][2:]
                if "=" in k:
                    k, value = k.split("=")
                    increment = 1
                elif i < len(param_list)-1 and not param_list[i+1].startswith("--"):
                    value = param_list[i + 1]
                    increment = 2
                else:
                    value = "true"
                    increment = 1
            else:
                raise RuntimeError(f"Cannot parse string {shell_string}")
        output_param_dict[k] = value
        i += increment

    return output_param_dict


def compare_version(v1: str, v2: str, version_checking: str) -> bool:
    """
    Compares v1 and v2 according to version checking which might be '>', '>=',
     '<', '<=', '=='

    :param v1: version to be compared
    :type v1: ``str``
    :param v2: version 2 to be compared
    :type v2: ``str``
    :param version_checking: Type of checking to be done. '>' means evaluation
                                for v1>v2
    :type version_checking: ``str``

    :return: Boolean result of evaluation
    :rtype: ``bool``
    """
    arr1 = v1.split(".")
    arr2 = v2.split(".")
    n = len(arr1)
    m = len(arr2)

    # converts to integer from string
    arr1 = [int(i) for i in arr1]
    arr2 = [int(i) for i in arr2]

    # compares which list is bigger and fills
    # smaller list with zero (for unequal delimiters)
    if n > m:
        for i in range(m, n):
            arr2.append(0)
    elif m > n:
        for i in range(n, m):
            arr1.append(0)

    # returns 1 if version 1 is bigger and -1 if
    # version 2 is bigger and 0 if equal
    comp = "="
    for i in range(len(arr1)):
        if arr1[i] > arr2[i]:
            comp = ">"
            break
        elif arr2[i] > arr1[i]:
            comp = "<"
            break

    return comp in version_checking
