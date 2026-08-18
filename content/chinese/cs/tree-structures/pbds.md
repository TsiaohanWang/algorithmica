---
title: GNU C++ PBDS 库
draft: true
---

下面这个结构需要以下库

``` C++
#include <ext/pb_ds/assoc_container.hpp> // 通用文件。
#include <ext/pb_ds/tree_policy.hpp> // 包含类 tree_order_statistics_node_update
```

以及

``` C++
using namespace __gnu_pbds;
```

有时我们不仅想要 set 能做的事，还想查询比如有多少数比我们的小，这时 `tree` 能帮上忙。

`tree` 模板的形式如下：

``` C++
template<
typename Key, // 键类型
typename Mapped, // 与键关联的数据类型
typename Cmp_Fn = std::less<Key>, // 比较函数子，应与运算符 < 一致
typename Tag = rb_tree_tag, // 标识树类型的标记
template<
typename Const_Node_Iterator,
typename Node_Iterator,
typename Cmp_Fn_,
typename Allocator_>
class Node_Update = null_node_update, // 顶点更新标记
typename Allocator = std::allocator<char> > // 分配器
class tree;
```

`Tag` 和 `Node_Update` 在普通 `map` 里是不存在的。

`Tag`——表示树结构的类。有三个类：`rb_tree_tag`、`splay_tree_tag` 和 `ov_tree_tag`。目前你不必知道它们是什么，只要知道你需要 `rb_tree_tag` 就够了。
`Node_Update`——表示在顶点里维护什么的类。最初是 `null_node_update`，一个什么都不存的类。但 C++ 里有 `tree_order_statistics_node_update`，它维护序统计量。

``` C++
typedef tree<
int,
null_type,
less<int>,
rb_tree_tag,
tree_order_statistics_node_update>
ordered_set;
```

这个容器拥有 set 的一切，此外还多了 `find_by_order()` 和 `order_of_key()`。前者返回第 $k$ 大元素的迭代器，后者给出集合中严格小于我们元素的元素个数。
