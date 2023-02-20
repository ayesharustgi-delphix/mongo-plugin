import shlex


def parse_shell_params(shell_string):
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


def compare_version(v1, v2, version_checking):
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
