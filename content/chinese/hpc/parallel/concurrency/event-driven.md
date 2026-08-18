---
title: 事件驱动并发
weight: 4
---

你可能在 JavaScript 中见过它。这类语言有一个不停运行的事件循环。它们也使用单线程，因为每个阻塞操作基本都是 I/O。

```js
var callback = function() {
    console.log("Button clicked")
}

document.getElementById('someButton').addEventListener("click", callback)
```

事件驱动环境通常是单线程的，通过「分片」（sharding）请求来实现多线程。

## Actor 模型

一种更通用的方法称为 *Actor 模型*。

它在 JVM 生态中非常流行。

```scala
import akka.actor.Actor
import akka.actor.ActorSystem
import akka.actor.Props

class HelloActor extends Actor {
  def receive = {
    case "hello" => println("hello back at you")
    case _       => println("huh?")
  }
}

object Main extends App {
  val system = ActorSystem("HelloSystem")
  // default Actor constructor
  val helloActor = system.actorOf(Props[HelloActor], name = "helloactor")
  helloActor ! "hello"
  helloActor ! "buenos dias"
}
```

使用消息代理（message broker）的一个非常重要的优势是，你可以解耦通信，还可以把 actor 迁移到另一个网络节点，从而实现分布式计算。