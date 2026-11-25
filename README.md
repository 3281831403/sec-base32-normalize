邀请码做校验时大小写混用，同一个码在两种写法下被当成两个不同的邀请：不折叠大小写，小写码被判非法；不映射易混字符，数字零与字母易混位被判不同；不去连字符，分组写法被判非法；填充补齐时不校验已有填充，双填充被接受；非法字符校验只查长度，杂字符通过；长度校验只判模八，模二与模四的非法长度通过；校验位算法用加法而不是模运算，碰撞率高；校验位字符表大小写不一致，输出与小写输入不匹配；归一不幂等，二次归一再补一次填充；批量归一复用折叠结果，第二个码沿用第一个码的大小写。codec/base32.py 是核心，tests/unit/test_base32.py 15个红。要修的是：按上面的顺序把 10 个缺陷逐个修掉。

运行方式

在仓库根目录执行：

    python -m pytest tests -q

当前状态是 15 failed，十五条失败的原因全部是 NotImplementedError。把 codec/base32.py 的八个桩实现之后，十五条测试应当全部转绿。

字段表

    题目类型：安全

仓库结构

    sec-base32-normalize/
        README.md
        conftest.py
        codec/
            __init__.py
            base32.py
        tests/
            unit/
                test_base32.py
            behaviour/
                test_base32_edge.py

codec/base32.py 是唯一实现文件，里面恰好八个桩，全部 raise NotImplementedError：

    strip_separators   去掉连字符与空白，保留其余字符
    fold_case          统一为大写
    map_lookalikes     把易混字符映射为规范字符
    validate_alphabet  返回问题列表，空列表表示通过
    add_padding        补齐填充到块边界，已对齐则不加
    check_digit        计算一位校验位，按模运算与约定字符表
    normalize          组合归一，输出不带连字符与填充
    code_batch         批量归一，各码独立

测试拆分布局

    tests/unit/test_base32.py 放十条契约测试，一条对一个缺陷，顺序与题面里十个缺陷的顺序完全一致。
    tests/behaviour/test_base32_edge.py 放五条边界测试：标准码归一后不变，小写与连字符写法归一后与标准码相同，非法字符被拒，校验位对单字符改动敏感，两批独立归一与单独归一相同。
    conftest.py 在仓库根，负责把仓库根加入 sys.path，因为 pytest 从仓库根采集 tests 目录，测试用绝对导入 codec.base32。
    题面里那句 tests/unit/test_base32.py 15个红 说的是整个测试集十五条全红，两个文件合起来正好十五条，十条在 unit，五条在 behaviour。

tests 不可修改

    测试文件就是判分依据，tests 目录下的任何文件都不许改，允许改的只有 codec/base32.py。
    测试的导入路径、常量与断言也不要动：十五条断言就是十个缺陷加五个边界的全部判据。

边角约定

    1. 字母表：0123456789ABCDEFGHJKMNPQRSTVWXYZ，三十二个字符，去掉易混的 I L O U。
    2. 大小写折叠：输入一律先折成大写，小写码不是非法码。fold_case 只转字母，连字符与数字原样保留。
    3. 易混字符映射：O 到 0，I 到 1，L 到 1，U 到 V，映射发生在大写折叠之后、字母表校验之前。map_lookalikes 只处理大写字母。
    4. 分隔符：连字符与各种空白都去掉，连续连字符视为多个分隔符，去掉后不留空位。strip_separators 保留其余字符。
    5. 填充规则：填充符是等号，只补到八字符块边界，已对齐则一个都不加。已有填充必须正好等于所需数量，多一个少一个都抛 ValueError，等号出现在中间同样抛 ValueError。
    6. 非法字符：validate_alphabet 逐字符比对字母表，不在表内的字符记一条以 illegal_char 开头的问题，问题里带上该字符。
    7. 长度校验：去掉末尾填充后的长度必须是八的整数倍。只满足模二或模四对齐的长度，例如十个字符与十二个字符，一律判非法，记一条以 bad_length 开头的问题。空串同样非法。
    8. 校验位：权重是奇数序列 1 3 5 7 等，第 i 位权重为 2i 加 1，从零起算。加权和对三十二取模，取模结果当下标，从字母表取一个字符。校验位必须取自大写表，小写输入也返回大写字符。
    9. 前导零：零是数据不是填充，前导零必须原样保留，0123-4567 归一成 01234567，不许截断也不许补零。
    10. 输出形状：normalize 输出全大写，不带连字符，不带填充，长度仍是八的整数倍。
    11. 幂等：normalize 的结果再过一遍 normalize 必须一字不变，不许再补一次填充。
    12. 批量：code_batch 每个码独立处理，不许复用前一个码的折叠或映射结果。policy 认三个键，keep_separators 缺省为假，with_check_digit 缺省为假，strict 缺省为真。strict 为假时非法码跳过，不写进结果。keep_separators 为真时从结果第一个字符起每四个一组插连字符，分组在追加校验位之前完成，校验位不参与分组。with_check_digit 为真时在结果末尾追加该码自身的校验位。返回的 dict 以输入码为键，保持输入顺序。

判分口径

    修完后 python -m pytest tests -q 应输出 15 passed。只改 codec/base32.py，不改 tests。

## 字段表

| 字段 | 取值 |
| --- | --- |
| 所属领域 | 安全 |
| 子方向 | 漏洞检测与攻防 |
| 任务类型 | Bugfix |
| 语言/框架 | Python 3, pytest |
| 环境可复现等级 | 无外部依赖 |

