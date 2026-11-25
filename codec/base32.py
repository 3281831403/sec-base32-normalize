"""base32 邀请码的编码规范化。

字母表是 Crockford 风格的三十二字符表，去掉易混的 I L O U：
    0123456789ABCDEFGHJKMNPQRSTVWXYZ

统一约定
    1. 一个码只由字母表字符组成，全部大写，长度是八的整数倍，不带连字符与填充。
    2. 分组写法每四个字符插一个连字符，连字符与空白在归一化时去掉。
    3. 易混字符先映射再校验：O 映到 0，I 与 L 映到 1，U 映到 V。
    4. 填充符是等号，只用于把不足一块的分片补到八字符边界，已对齐不得再加。
    5. 校验位是各字符值的加权和对三十二取模，权重为奇数 1 3 5 7 ...，
       取模结果当下标，从字母表取字符，输出必为大写。
    6. 前导零是数据的一部分，必须原样保留。
"""

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
BLOCK_SIZE = 8
PADDING = "="
LOOKALIKES = {"O": "0", "I": "1", "L": "1", "U": "V"}

# 字符 -> 数值，供校验位加权求和使用。
_CHAR_VALUE = {ch: i for i, ch in enumerate(ALPHABET)}


def strip_separators(text: str) -> str:
    """去掉连字符与空白，保留其余字符。"""
    return "".join(ch for ch in text if ch != "-" and not ch.isspace())


def fold_case(text: str) -> str:
    """把字母统一为大写，其余字符原样保留。"""
    return text.upper()


def map_lookalikes(text: str) -> str:
    """把易混字符映射为规范字符：O 到 0，I 与 L 到 1，U 到 V。

    只处理大写字母，小写字母应先经 fold_case。
    """
    return "".join(LOOKALIKES.get(ch, ch) for ch in text)


def validate_alphabet(text: str) -> list[str]:
    """返回问题列表，空列表表示通过。

    去掉末尾填充后逐字符检查：不在字母表里的字符记一条以 illegal_char 开头的问题；
    去掉末尾填充后的长度不是八的整数倍记一条以 bad_length 开头的问题，
    只满足模二或模四对齐的长度同样非法。
    """
    problems: list[str] = []

    # 末尾填充不参与字符与长度校验；中间的等号会保留并按非法字符处理。
    core = text.rstrip(PADDING)

    for ch in core:
        if ch not in _CHAR_VALUE:
            problems.append(f"illegal_char: 字符 {ch!r} 不在 base32 字母表中")

    if len(core) == 0 or len(core) % BLOCK_SIZE != 0:
        problems.append(
            f"bad_length: 去掉末尾填充后长度为 {len(core)}，"
            f"必须是非零的 {BLOCK_SIZE} 的整数倍"
        )

    return problems


def add_padding(text: str) -> str:
    """把文本补齐到八字符块边界，已对齐则不加。

    已有填充时必须正好等于所需数量，多余或不足都抛 ValueError；
    等号出现在中间也抛 ValueError。
    """
    first_pad = text.find(PADDING)

    if first_pad == -1:
        needed = (-len(text)) % BLOCK_SIZE
        return text + PADDING * needed

    # 第一个等号之后只允许继续出现等号，否则就是填充落在了中间。
    base = text[:first_pad]
    suffix = text[first_pad:]
    if any(ch != PADDING for ch in suffix):
        raise ValueError("invalid_padding: 填充符 '=' 只能出现在末尾")

    existing = len(suffix)
    needed = (-len(base)) % BLOCK_SIZE
    if existing != needed:
        raise ValueError(
            f"invalid_padding: 数据长度 {len(base)} 需要 {needed} 个填充符，"
            f"实际有 {existing} 个"
        )

    return text


def check_digit(text: str) -> str:
    """计算一位校验位，返回大写字符。

    先折叠大小写、映射易混字符，再按奇数权重求加权和并对三十二取模，
    取模结果当下标从字母表取字符。
    """
    canonical = map_lookalikes(fold_case(text))
    weighted_sum = sum(
        _CHAR_VALUE[ch] * (2 * i + 1) for i, ch in enumerate(canonical)
    )
    return ALPHABET[weighted_sum % len(ALPHABET)]


def normalize(text: str) -> str:
    """组合归一，输出不带连字符与填充的大写码。

    依次去分隔符、折叠大小写、映射易混字符、校验字符与长度，
    非法输入抛 ValueError；归一必须幂等。
    """
    canonical = map_lookalikes(fold_case(strip_separators(text)))

    problems = validate_alphabet(canonical)
    if problems:
        raise ValueError("; ".join(problems))

    # 规范输出不带填充；校验已保证去填充后的长度是八的整数倍。
    return canonical.rstrip(PADDING)


def _group_four(canonical: str) -> str:
    """从第一个字符起每四个字符插一个连字符。"""
    return "-".join(
        canonical[i : i + 4] for i in range(0, len(canonical), 4)
    )


def code_batch(codes, policy) -> dict:
    """批量归一，各码独立处理，返回输入码到归一结果的 dict。

    policy 支持的键与缺省值
        keep_separators: False   为真时每四个字符插一个连字符
        with_check_digit: False  为真时在末尾追加一位校验位
        strict: True             为真时遇到非法码立即抛 ValueError，
                                 为假时跳过非法码，不写入结果
    """
    policy = policy or {}
    keep_separators = policy.get("keep_separators", False)
    with_check_digit = policy.get("with_check_digit", False)
    strict = policy.get("strict", True)

    result: dict = {}
    for code in codes:
        try:
            canonical = normalize(code)
        except ValueError:
            if strict:
                raise
            continue

        # 校验位基于不带分隔符的规范码计算。
        digit = check_digit(canonical) if with_check_digit else None

        # 先分组，再把校验位追加到末尾：校验位不参与四位分组。
        value = _group_four(canonical) if keep_separators else canonical
        if with_check_digit:
            value += digit

        result[code] = value

    return result
