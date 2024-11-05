运行环境为
Linux                    Linux isumi-Lenovo-16 6.8.0-47-generic #47~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Oct  2 16:16:55 UTC 2 x86_64 x86_64 x86_64 GNU/Linu
stanza                   1.9.2
neo4j                    5.25.0
Python                   3.8.18

安装 neo4j
sudo apt update
安装 Neo4j 的第一步是添加 GPG 密钥。
curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/neo4j.gpg
将 Neo4j 存储库添加到您的系统 APT 源目录。
echo "deb [signed-by=/usr/share/keyrings/neo4j.gpg] https://debian.neo4j.com stable latest" | sudo tee -a /etc/apt/sources.list.d/neo4j.list
为避免升级到下一个主要版本的风险，您可以在上述命令中指定所需的主要和次要版本来代替 latest。
以下命令将添加 Neo4j 5.x 存储库，这意味着无论何时发布，您都不会升级到 6.x 版本。
echo "deb [signed-by=/usr/share/keyrings/neo4j.gpg] https://debian.neo4j.com stable 5" | sudo tee -a /etc/apt/sources.list.d/neo4j.list
更新系统存储库列表。 
sudo apt update
安装 Neo4j 社区版。
sudo apt install neo4j
启动服务并设为开机自启
sudo systemctl start neo4j
sudo systemctl enable neo4j
通过http://localhost:7474访问
初始卡密为neo4j/neo4j

需要安装的支持
pip install neo4j
pip install stanza

切换数据库
原理为切换一个新的默认数据库，顶掉原来的数据库，但是原来的不会被删除
打开配置文件
sudo nano /etc/neo4j/neo4j.conf
找到 #initial.dbms.default_database=neo4j
将 neo4j 改为自己的新数据库名后取消注释
运行下面的命令重启数据库即可
sudo systemctl restart neo4j

清空数据库
MATCH (n)
DETACH DELETE n

不包含 NER 命名实体识别
main0:
    实体：
        Virus - 用于表示病毒类别。
        病毒名称（例如：ExampleVirus） - 用于表示具体的病毒实例。
    属性值实体（因其动态变化，不是固定实体）：
        aliases 的值（病毒的别名列表）
        discovery_date 的值（发现日期）
        length 的值（病毒的长度）
        origin 的值（病毒的来源）
        risk_assessment 的值（风险评估）
        minimum_dat 的值（最低DAT版本）
        dat_release_date 的值（DAT版本发布日期）
        symptoms 的值（症状）
        method_of_infection 的值（感染方法）
        removal_instructions 的值（移除指令）
    关系：
        "is_a" - 用于表示实体的分类关系，例如病毒是一种"Virus"。
        "has_aliases" - 用于表示病毒的别名。
        "has_discovery_date" - 用于表示病毒的发现日期。
        "has_length" - 用于表示病毒的长度。
        "has_origin" - 用于表示病毒的来源。
        "has_risk_assessment" - 用于表示病毒的风险评估。
        "has_minimum_dat" - 用于表示病毒的最低DAT版本。
        "has_dat_release_date" - 用于表示DAT版本的发布日期。
        "has_symptoms" - 用于表示病毒的症状。
        "has_method_of_infection" - 用于表示病毒的感染方法。
        "has_removal_instructions" - 用于表示病毒的移除指令。


含有 Stanza NER 命名实体识别
main:
    实体:
        Virus - 用于表示病毒类别。
        病毒名称 - 用于表示具体的病毒实例。
        Entity - 用于表示通用的实体节点，名字来源于文本处理的对象。
    动态提取的实体:
        文本处理过程中提取的实体类型：ORG、PRODUCT、QUANTITY、CARDINAL、DISEASE 等。
    属性值实体:
        aliases 的值（别名）
        discovery_date 的值（发现日期）
        length 的值（长度）
        origin 的值（来源）
        risk_assessment 的值（风险评估）
        minimum_dat 的值（最低DAT版本）
        dat_release_date 的值（DAT版本发布日期）
        symptoms 的值（症状）
        method_of_infection 的值（感染方法）
        removal_instructions 的值（移除指令）
        file_length_increase 的文件类型（根据特征文本提取）
    关系:
        "is_a" - 用于表示实体的分类关系，例如病毒是一种"Virus"。
        "has_aliases" - 用于表示病毒的别名。
        "has_discovery_date" - 用于表示病毒的发现日期。
        "has_length" - 用于表示病毒的长度。
        "has_origin" - 用于表示病毒的来源。
        "has_risk_assessment" - 用于表示病毒的风险评估。
        "has_minimum_dat" - 用于表示病毒的最低DAT版本。
        "has_dat_release_date" - 用于表示DAT版本的发布日期。
        "has_symptoms" - 用于表示病毒的症状。
        "has_method_of_infection" - 用于表示病毒的感染方法。
        "has_removal_instructions" - 用于表示病毒的移除指令。
    动态提取的关系
        从文本中提取的基于动词的关系，采用(subject, relation, object)形式。
        从文本中提取的属性关系，例如("size", "has", size_value)。