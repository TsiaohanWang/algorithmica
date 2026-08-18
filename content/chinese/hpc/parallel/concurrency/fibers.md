---
title: 纤程
weight: 3
---

*纤程*（fiber）是由语言本身实现的轻量级线程。它们的工作方式是随时从上次中断的地方接着执行。因此语言必须维护自己的运行时。

```go
package main

import (
	"fmt"
	"time"
)

func say(s string) {
	for i := 0; i < 5; i++ {
		time.Sleep(100 * time.Millisecond)
		fmt.Println(s)
	}
}

func main() {
	go say("world")
	say("hello")
}
```

其工作方式是，语言维护一组线程，随时准备从它们上次停下的地方继续。这被称为 N:M 调度。

其他语言也有类似的运行时，例如 C++ 和 Rust。