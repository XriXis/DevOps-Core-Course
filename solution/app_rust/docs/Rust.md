# Lab 01 — DevOps Info Service: Language Selection

## 1. Language Choice

For this lab, I chose **Rust** as the implementation language.

**Reasons:**

* **Memory safety without garbage collector:** Rust ensures safety at compile-time using its ownership and borrowing system.
* **High performance:** Rust can achieve speeds close to C/C++.
* **Modern ecosystem for web development:** Actix-web and Warp provide asynchronous, type-safe frameworks.
* **Strong typing and compiler guarantees:** Many runtime errors are caught at compile time.
* **Growing community and industry adoption:** Rust is increasingly used for systems programming and backend services.

**Comparison with alternatives:**

| Language | Pros                                                    | Cons                                                 |
| -------- | ------------------------------------------------------- | ---------------------------------------------------- |
| Go       | Simple syntax, fast compilation, built-in concurrency   | Less strict type safety, garbage collected           |
| Java     | Mature ecosystem, vast library support, JVM portability | Verbose syntax, GC pauses may occur                  |
| C#       | Modern syntax, good async support, strong tooling       | Mainly Windows-centric historically, heavier runtime |
| Rust     | Memory safety, zero-cost abstractions, high performance | Steeper learning curve, longer compilation times     |

## 2. Expected Benefits

* **Reliable system-level programming** without runtime memory errors.
* **High-performance web service** capable of handling many concurrent requests.
* **Strong static typing** reduces bugs and improves maintainability.
* **Modern async frameworks** like Actix-Web allow writing scalable APIs.

## 3. Notes

* The Rust choice aligns with goals for **high performance**, **safety**, and **concurrency**.
* Future labs may explore Rust-specific features like **ownership**, **lifetimes**, and **async programming**.
* While Go and Java could also implement the service easily, Rust provides **more control over memory and runtime behavior**, which is valuable in systems-level DevOps services.

