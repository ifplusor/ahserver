# PEP 333 - Python Web Server Gateway Interface v1.0 中文版

> 翻译自 `Python Web Server Gateway Interface v1.0` [PEP 333 - Python Web Server Gateway Interface v1.0](https://www.python.org/dev/peps/pep-0333/)

## 目录

- [目录](#目录)
- [序言 (Preface)](#序言-preface)
- [摘要 (Abstract)](#摘要-abstract)
- [基本原理及目标 (Rationale and Goals)](#基本原理及目标-rationale-and-goals)
- [规范概述 (Specification Overview)](#规范概述-specification-overview)
  - [*应用程序/框架*端 (The Application/Framework Side)](#应用程序框架端-the-applicationframework-side)
  - [*服务器/网关*端 (The Server/Gateway Side)](#服务器网关端-the-servergateway-side)
  - [中间件：可扮演两端角色的组件 (Middleware: Components that Play Both Sides)](#中间件可扮演两端角色的组件-middleware-components-that-play-both-sides)
- [规范细则 (Specification Details)](#规范细则-specification-details)
  - [`environ`变量 (`environ` Variables)](#environ变量-environ-variables)
    - [输入流和错误流 (Input and Error Streams)](#输入流和错误流-input-and-error-streams)
  - [`start_response()`函数 (The `start_response()` Callable)](#start_response函数-the-start_response-callable)
  - [处理`Content-Length`首部 (Handling the `Content-Length` Header)](#处理content-length首部-handling-the-content-length-header)
  - [缓冲和流 (Buffering and Streaming)](#缓冲和流-buffering-and-streaming)
    - [中间件的块边界处理 (Middleware Handling of Block Boundaries)](#中间件的块边界处理-middleware-handling-of-block-boundaries)
    - [`write()`函数 (The `write()` Callable)](#write函数-the-write-callable)
  - [Unicode问题 (Unicode Issues)](#unicode问题-unicode-issues)
  - [错误处理 (Error Handling)](#错误处理-error-handling)
  - [HTTP 1.1 Expect/Continue 机制 (HTTP 1.1 Expect/Continue)](#http-11-expectcontinue-机制-http-11-expectcontinue)
  - [HTTP的其他特性 (Other HTTP Features)](#http的其他特性-other-http-features)
  - [线程支持 (Thread Support)](#线程支持-thread-support)
- [具体实现/应用程序备注 (Implementation/Application Notes)](#具体实现应用程序备注-implementationapplication-notes)
  - [服务器扩展APIs (Server Extension APIs)](#服务器扩展apis-server-extension-apis)
  - [应用程序配置 (Application Configuration)](#应用程序配置-application-configuration)
  - [URL的重建 (URL Reconstruction)](#url的重建-url-reconstruction)
  - [对旧版本Python(2.2之前)的支持 (Supporting Older Versions of Python)](#对旧版本python22之前的支持-supporting-older-versions-of-python)
  - [可选的平台相关文件处理 (Optional Platform-Specific File Handling)](#可选的平台相关文件处理-optional-platform-specific-file-handling)
- [问答环节 (Questions and Answers)](#问答环节-questions-and-answers)
- [尚在讨论中的提议 (Proposed/Under Discussion)](#尚在讨论中的提议-proposedunder-discussion)
- [鸣谢 (Acknowledgements)](#鸣谢-acknowledgements)
- [参考文献 (References)](#参考文献-references)
- [版权 (Copyright)](#版权-copyright)

## 序言 (Preface)

注意：关于本规范的后续版本，请参照[PEP 3333](https://www.python.org/dev/peps/pep-3333)，PEP 3333是支持Python 3.x的新版本，同时还包含了一些社区勘误，补充，更正的相关说明信息。

## 摘要 (Abstract)

这份规范规定了一种在web服务器与web应用程序/框架之间推荐的标准接口，以确保web应用程序在不同的web服务器之间具有可移植性。

## 基本原理及目标 (Rationale and Goals)

Python目前拥有大量的web框架，比如Zope、Quixote、Webware、SkunkWeb、PSO和Twisted Web——这里我仅列举出这么几个[[1]](#reference-1)。这么多的选择让新手无所适从，因为整体上，选择什么样的框架有时会反过来限制对web服务器的选择。

相比之下，虽然java也拥有众多web的框架，但是java的**servlet API**使得用任何框架编写出来的应用程序都可以在所有支持**servlet API**的web服务器上运行。

服务器中这种针对Python的API的使用和普及（**不管服务器是用python写的（如: Medusa），还是内嵌python（如: mod_python），亦或是通过一种网关协议来调用Python（如:CGI, FastCGI等）**），把人们从web框架的选择和web服务器的选择中剥离开来，使他们能够任意选择适合自己的组合，而web服务器和web框架的开发者们也能够把精力集中到各自的领域。  

鉴于此，这份PEP建议在web服务器和web应用程序/web框架之间建立一种简单通用的接口规范，即Python Web服务器网关接口（简称WSGI）。

但是光有这么一份规范，对于改变web服务器和web应用程序/框架的现状还是不够的，只有当那些web服务器和web框架的作者/维护者们真正地实现了WSGI，这份WSGI规范才能起到它该起的作用。  

不过，由于目前还没有任何框架或服务器实现了WSGI，而那些新转向支持WSGI的框架作者们也不会从我们这得到任何直接的奖励或者好处，所以，我们的这份WSGI**必须**要拟定得足够容易实现，这样才能降低框架作者们在实现接口这件事上的初始投资成本。

由此可见，服务器和框架两边接口实现的简单性，对于提高WSGI的实用性来说，绝对是非常重要的，同时，这一点也是任何设计决策的首要依据。

然而需要注意的是，框架作者实现框架时的简单性和web应用程序开发者使用框架时的易用性是两码事。WSGI为框架作者们提出了一套只包含必需、最基本元素的接口，因为像响应对象以及 cookie 处理等这些花哨的高级功能只会妨碍现有的框架对这些问题的处理。再说一次，WSGI的目标是使现有的web服务器和web框架之间更加方便地互联互通，而不是想重新创建一套新的web框架。

同时也要注意到，我们的这个目标也限制了WSGI不会用到任何当前版本的Python里没有的东西。因此，这一份规范中不会推荐或要求任何新的Python标准模块，WSGI中规定的所有东西都不需要2.2.2以上版本的Python支持。（当然，在未来版本的Python标准库中，倘若Python自带的标准库中的Web服务器能够包含对我们这份接口的支持，那将会是一个很不错的主意。)

除了要让现有的以及将要出现的框架和服务器容易实现之外，也应该让创建诸如请求预处理器`(request preprocessors)`、响应处理器`(response postprocessors)`及其他基于WSGI的中间件组件这一类事情变得简单易操作。这里说的中间件组件，它们是这样一种东西：对服务器来说它们是应用程序，而对中间件包含的应用程序来说，它们又可以被看作是服务器。

如果中间件既简单又鲁棒，并且WSGI可以广泛地应用在服务器和框架中，那么就有可能出现全新的Python web框架：一个由若干个WSGI中间件组件组成的松耦合的框架。事实上，现有框架的作者们甚至可能会选择去重构他们框架中已有的服务，使它们变得更像是一些配合WSGI使用的库而不是一个完整的框架。这样一来，web应用程序开发者们这就可以为他们想实现的特定功能选择最佳组合的组件，而不用再局限于某一个特定框架并忍受该框架的所有优缺点。

当然，就现在来说，这一天毫无疑问还要等很久。同时，对WSGI来说，让每一个框架都能在任何服务器上运行起来，又是一个十足的短期目标。

最后，需要指出的是，此版本的WSGI对于一个应用程序具体该以何种方式部署在web服务器或者服务器网关上并没有做具体说明。就现在来看，这个是需要由服务器或网关来负责定义怎么实现的。等到以后，等有了足够多的服务器/网关通过实现了WSGI并积累了多样化的部署需求方面的领域经验，那么到时候也许会产生另一份PEP来描述WSGI服务器和应用框架的部署标准。

## 规范概述 (Specification Overview)

WSGI接口可以分为两端：服务器/网关端和应用程序/Web框架端。服务器端调用一个由应用程序端提供的可调用对象`(Callable)`，至于它是如何被调用的，这要取决于服务器/网关这一端。我们假定有一些服务器/网关会要求应用程序的部署人员编写一个简短的脚本来启动一个服务器/网关的实例，并提供给服务器/网关一个应用程序对象，而还有的一些服务器/网关则不需要这样，它们会需要一个配置文件又或者是其他机制来指定应该从哪里导入或者获得应用程序对象。

除了单纯的服务器/网关和应用程序/框架，还可以创建一种叫做中间件的组件，中间件它对这份规范当中的两端(服务器端和应用程序端)都做了实现，我们可以这样解释中间件，对于包含它们的服务器，中间件是应用程序，而对于包含在中间件当中的应用程序来说，它又扮演着服务器的角色。不仅如此，中间件还可以用来提供可扩展的API，以及内容转换，导航和其他有用的功能。

在这份规范说明书中，我们将使用的术语`“可调用对象(a callable)”`，它的意思是“**一个函数，方法，类或者拥有`__call__`方法的一个对象实例**”，这取决于服务器，网关或者应用程序根据需要而选择的合适的实现技术。相反，服务器，网关或者请求一个可调用对象`(callable)`的应用程序**必须不**依赖可调用对象`(callable)`的具体提供方式。记住，可调用对象`(callable)`只是被调用，不会自省`(introspect)`。[**译者注：introspect，自省，Python的强项之一，指的是代码可以在内存中象处理对象一样查找其它的模块和函数。**]

### *应用程序/框架*端 (The Application/Framework Side)

一个应用程序对象简单地说就是一个接受了2个参数的可调用对象`(callable object)`，这里的对象并不能理解为它真的需要一个对象实例：一个函数、方法、类或者带有`__call__`方法的对象实例都可以用来当做应用程序对象。应用程序对象必须可以被多次调用，实质上所有的服务器/网关（除了CGI）都会产生这样的重复请求。

（注意：虽然我们把它叫做“应用程序”对象，但这并不意味着程序员需要把WSGI当做API来调用！我们假定应用程序开发者将会仍然使用更高层的框架服务来开发它们的应用程序，WSGI只是一个提供给框架和服务器开发者们使用的工具，它并没有打算直接向应用程序开发者提供支持。)

这里我们来看两个应用程序对象的示例：其中，一个是函数，另一个是类：

```python
def simple_app(environ, start_response):
    """这可能是最简单的应用程序对象了。"""
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return ['Hello world!\n']


class AppClass:
    """生成相同的输出，但是使用的是一个类。

    （注意：这里‘AppClass’就是一个“应用程序”，故调用它会返回一个‘AppClass’的实例，
    这个实例就是规范里面说的由一个“可调用的应用程序(application callable)”返回的
    可迭代者(iterable)。

    如果我们希望使用‘AppClass’的实例，而不是应用程序对象，那么我们就必须实现这个
    ‘__call__’方法，这个方法将用来执行应用程序，然后我们需要创建一个实例来提供给
    服务器/网关使用。
    """

    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def __iter__(self):
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        self.start(status, response_headers)
        yield "Hello world!\n"
```

### *服务器/网关*端 (The Server/Gateway Side)

每一次，当HTTP客户端冲着应用程序发来一个请求，服务器/网关都会调用应用程序的可调用对象`(callable)`。为了阐述方便，这里有一个CGI网关，简单的说它就是一个以应用程序对象为参数的函数实现，注意，本例中对错误只做了有限的处理，因为默认情况下没有被捕获到的异常都会被输出到`sys.stderr`并被服务器记录下来。

```python
import os, sys

def run_with_cgi(application):

    environ = dict(os.environ.items())
    environ['wsgi.input']        = sys.stdin
    environ['wsgi.errors']       = sys.stderr
    environ['wsgi.version']      = (1, 0)
    environ['wsgi.multithread']  = False
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once']     = True

    if environ.get('HTTPS', 'off') in ('on', '1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'

    headers_set = []
    headers_sent = []

    def write(data):
        if not headers_set:
             raise AssertionError("write() before start_response()")

        elif not headers_sent:
             # 在第一次输出之前发送已存储的报头。
             status, response_headers = headers_sent[:] = headers_set
             sys.stdout.write('Status: %s\r\n' % status)
             for header in response_headers:
                 sys.stdout.write('%s: %s\r\n' % header)
             sys.stdout.write('\r\n')

        sys.stdout.write(data)
        sys.stdout.flush()

    def start_response(status, response_headers, exc_info=None):
        if exc_info:
            try:
                if headers_sent:
                    # 如果报头已发送，则重新抛出原始的异常。
                    raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                exc_info = None  # 避免死循环。
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set[:] = [status, response_headers]
        return write

    result = application(environ, start_response)
    try:
        for data in result:
            if data:   # 在报文体出现前不发送报头。
                write(data)
        if not headers_sent:
            write('')  # 如果报文体为空，则发送报头。
    finally:
        if hasattr(result, 'close'):
            result.close()
```

### 中间件：可扮演两端角色的组件 (Middleware: Components that Play Both Sides)

我们注意到，单个对象可以作为请求应用程序的服务器存在，也可以作为被服务器调用的应用程序存在。这样的“中间件”可以执行以下这些功能：

- 在相应地重写`environ`变量之后，根据目标URL地址将请求路由到不同的应用程序对象。
- 允许多个应用程序或框架在同一个进程中并行运行。
- 通过在网络上转发请求和应答，实现负载均衡和远程处理。
- 对上下文（content）进行后加工（postprocessing），比如应用xsl样式表等。

中间件的存在对于“服务器/网关”和“应用程序/框架”来说是透明的，并不需要特殊的支持。希望在应用程序中加入中间件的用户只须简单地把中间件当作应用程序提供给服务器，并配置中间件组件以服务器的身份来调用应用程序。当然，中间件组件包裹的“应用程序”也可能是另外一个包裹了应用程序的中间件组件，这样循环下去就构成了我们所说的“中间件栈”了。

最重要的别忘了，中间件必须遵循WSGI的服务器和应用程序两端提出的一些限制和要求，甚至有些时候，对中间件的要求比对单纯的服务器或应用程序还要严格，关于这些我们都会在这份规范文档中指出来。

这里有一个（有趣的）中间件组件的例子，这个中间件使用*Joe Strout*写的`piglatin.py`程序将`text/plain`的响应转换成`pig latin`**[译者注:意思是将英语词尾改成拉丁语式]**。（注意：一个“真实”的中间件组件很可能会使用更加鲁棒的方式来检查内容`(content)`的类型和内容`(content)`的编码。同样，这个简单的例子还忽略了一个单词还可能跨区块分割的可能性）

```python
from piglatin import piglatin

class LatinIter:

    """将可迭代的输出转换成拉丁语式，如果可以转换的话。

    注意“okayness”可能改变，直到应用程序生成(yield)出它自己的第一个非空字符串，
    所以，‘transform_ok’必须是一个可变的真实值。
    """

    def __init__(self, result, transform_ok):
        if hasattr(result, 'close'):
            self.close = result.close
        self._next = iter(result).next
        self.transform_ok = transform_ok

    def __iter__(self):
        return self

    def next(self):
        if self.transform_ok:
            return piglatin(self._next())
        else:
            return self._next()

class Latinator:

    # 默认情况下不传送输出。
    transform = False

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):

        transform_ok = []

        def start_latin(status, response_headers, exc_info=None):

            # 重置ok标志位，以防这是一个重复的调用。
            del transform_ok[:]

            for name, value in response_headers:
                if name.lower() == 'content-type' and value == 'text/plain':
                    transform_ok.append(True)
                    # 若出现content-length，则需要strip，否则会出错。
                    response_headers = [(name, value)
                        for name, value in response_headers
                            if name.lower() != 'content-length'
                    ]
                    break

            write = start_response(status, response_headers, exc_info)

            if transform_ok:
                def write_latin(data):
                    write(piglatin(data))
                return write_latin
            else:
                return write

        return LatinIter(self.application(environ, start_latin), transform_ok)


# 在Latinator's控制下运行foo_app, 使用示例的CGI网关例子。
from foo_app import foo_app
run_with_cgi(Latinator(foo_app))
```

## 规范细则 (Specification Details)

应用程序对象必须接受两个位置参数（positional arguments），为了方便说明，我们不妨将它们分别命名为`environ`和`start_response`，但是这并不是说它们必须取这两个名字。服务器或网关**必须**用这两个位置参数（注意不是关键字参数）来调用应用程序对象（比如，像上面展示的那样调用`result = application(environ,start_response)`）

`environ`参数是一个字典对象，也是一个有着CGI风格的环境变量。这个对象**必须**是一个Python内建的字典对象（*不*能是子类、用户字典`(UserDict)`或其他对字典对象的模仿），应用程序必须允许以任何它需要的方式来修改这个字典， `environ`还必须包含一些特定的WSGI所需的变量（在后面章节里会提到），有时也可以包含一些服务器相关的扩展变量，通过下文提到的命名规范来命名。
  
`start_response`参数是一个可调用对象`(callable)`，它接受两个必须的位置参数和一个可选参数。为方便说明，我们分别将它们命名为`status`，`response_headers`和`exc_info`。再强调一遍，这并不是说它们一定要用这些名字。应用程序**必须**用这些位置参数来调用`start_response`（比如像这样：`start_response(status,response_headers)`)。

`status`参数是形式如`"999 Message here"`的状态字符串。`response_headers`参数是包含`(header_name, header_value)`元组的列表，用来描述HTTP的响应头。可选的`exc_info`参数会在接下来的[`start_response()`函数](#start_response函数-the-start_response-callable)和[错误处理](#错误处理-error-handling)两节中详细描述，它只有在应用程序捕获到了错误并试图在浏览器中显示错误的时候才会被用到。

`start_response`必须返回一个形如`write(body_data)`的可调用对象`(callable)`，它接受一个位置参数：一个将会被当作HTTP响应体的一部分而输出的字符串（注意：提供`write()`只是为了支持一些现有框架的命令式输出APIs；新的应用程序或框架应当尽量避免使用`write()`，详细情况请参照[缓冲和流](#缓冲和流-buffering-and-streaming)章节。)

当应用程序被服务器调用的时候，它必须返回一个能够生成0个或多个字符串的可迭代对象`(iterable)`。可以通过几种方式来实现，比如通过返回一个包含一系列字符串的列表，或者是让应用程序本身就是一个能生成多个字符串的生成器`(generator)`，又或者是使应用程序本身是一个类并且这个类的实例是一个可迭代对象`(iterable)`。总之，不论通过什么途径完成，应用程序对象必须总是能返回一个能够生成0个或多个字符串的可迭代对象`(iterable)`。

服务器或者网关必须将产生的字符串以一种无缓冲的方式传送到客户端，并且总是在一个字符串传完之后再去请求下一个字符串。（换句话说，也就是应用程序**应该**自己负责实现缓冲机制。更多关于应用程序输出应该如何处理的细节，请阅读下文的[缓冲和流](#缓冲和流-buffering-and-streaming)章节。)

服务器或网关应当将产生的字符串看做是一串*二进制字节序列*来对待：特别地，它必须确保行的结尾没有被修改。应用程序必须负责确保将那些要传送至HTTP客户端的字符串以一种与客户端相匹配的编码方式输出（服务器/网关**可能**会对HTTP附加传输编码，或者为了实现一些类似字节范围传输`(byte-range transmission)`这样的HTTP特性而进行一些转换，更多关于HTTP特性的细节请参照下文的[HTTP的其他特性](#http的其他特性-other-http-features)章节。)

假如服务器成功调用了`len(iterable)`方法，则它会认为此结果是正确的并且信赖这个结果。也就是说，如果应用程序返回的可迭代对象`(iterable)`字符串提供了一个可用的`__len__()` 方法，那么服务器就会假定应用程序**必然**返回了正确的结果。（关于这个方法在一般情况下是如何被使用的，请阅读下文的[处理Content-Length头](#处理content-length头-handling-the-content-length-header)。)

如果应用程序返回的可迭代对象`(iterable)`有一个叫做`close()`的方法，则不论当前的请求是正常结束还是由于异常而终止，服务器/网关都**必须**在结束该请求之前调用这个方法。（这么做的目的是为了支持应用程序端的资源释放，这份规范将尝试完善对[PEP 325](https://www.python.org/dev/peps/pep-0325/)中生成器的支持，以及其它有`close()`方法的通用可迭代对象`(iterable)`的支持。

（注意：应用程序**必须**在可迭代对象`(iterable)`产生第一个报文主体`(body)`字符串之前请求`start_response()`，这样服务器才能在发送任何报文主体`(body)`内容之前发送响应首部`(headers)`。不过，这一调用也**可能**在可迭代对象`(iterable)`第一次迭代的时候执行，所以服务器**不能**假定在它们开始迭代之前`start_response()`已经被调用过了。)

最后要说的是，服务器和网关**不能**使用应用程序返回的可迭代对象`(iterable)`的任何其他属性，除非是针对服务器或网关的特定类型的实例，比如`wsgi.file_wrapper`返回的“file wrapper”（请阅读[可选的平台相关文件处理](#可选的平台相关文件处理-optional-platform-specific-file-handling)章节)。通常情况下，只有在这里指定的属性，或者通过[PEP 234 iteration APIs](https://www.python.org/dev/peps/pep-0234/)访问的属性才是可以接受的。

### `environ`变量 (`environ` Variables)

`environ`字典被用来包含这些CGI环境变量，这些变量定义可以在参考文献*Common Gateway Interface specification*[[2]](#reference-2)中找到。下面所列出的这些变量若不是空字符串，都**必须**被设置。否则（为空字符串），若无特殊说明，它们**可以**被忽略。

------

**REQUEST_METHOD**  
HTTP的请求方法，如`"GET"`或`"POST"`。这个参数永远不可能是空字符串，故必须被设置。

------

**SCRIPT_NAME**  
URL请求中“路径`(path)`”的开始部分，对应了应用程序对象，这样应用程序就知道它的虚拟位置。如果该应用程序对应服务器根目录的话， 那么`SCRIPT_NAME`的值可能为空字符串。

------

**PATH_INFO**  
URL请求中“路径`(path)`”的其余部分，指定请求的目标在应用程序内部的虚拟位置。如果请求的目标是应用程序根目录并且末尾没有`'/'`符号结尾的话，那么`PATH_INFO`可能为空字符串 。

------

**QUERY_STRING**  
URL请求中紧跟在`'?'`后面的那部分，它可以为空或不存在。

------

**CONTENT_TYPE**  
HTTP请求中`Content-Type`字段包含的所有内容，它可以为空或不存在。

------

**CONTENT_LENGTH**  
HTTP请求中`Content-Length`字段包含的所有内容，它可以为空或不存在。

------

**SERVER_NAME**，**SERVER_PORT**  
这两个变量可以和`SCRIPT_NAME`、`PATH_INFO`一起构成了一个完整的URL。然而要注意的是，如果有出现`HTTP_HOST`，那么在重建URL请求的时候就应当优先使用`HTTP_HOST`而非`SERVER_NAME`。详细内容请阅读下文的[URL的重建](#url的重建-url-reconstruction)章节 。`SERVER_NAME`和`SERVER_PORT`这两个变量永远不可能是空字符串，故它们必须被设置。

------

**SERVER_PROTOCOL**  
客户端发送请求的时候所使用的协议版本。通常是类似`"HTTP/1.0"`或`"HTTP/1.1"`这样的字符串，可以被应用程序用来判断如何处理HTTP请求报头。（事实上这个变量更应该被叫做`REQUEST_PROTOCOL`，因为这个变量代表的是在请求中使用的协议，而且和服务器响应时使用的协议毫无关系。但为了保持和CGI的兼容性，这里我们还是沿用已有的名字`SERVER_PROTOCOL`）

------

**HTTP_变量组**  
这组变量对应着客户端提供的HTTP请求首部`(headers)`（即那些名字以`"HTTP_"`开头的变量）。这组变量的存在与否应和HTTP请求中相对应的HTTP首部字段保持一致。

------

一个服务器或网关**应该**尽可能多地提供其他可用的CGI变量。另外，如果启用了SSL，服务器或网关也**应该**尽可能地提供可用的Apache SSL环境变量[[5]](#reference-5)，比如`HTTPS=on`和`SSL_PROTOCOL`。不过要注意的是，假如一个应用程序使用了些上述没有列出的变量，那么对于那些不支持相关扩展的服务器来说，就必然要考虑到不可移植的缺点（比如，不发布文件的web服务器就没法提供一个有意义的`DOCUMENT_ROOT`和`PATH_TRANSLATED`变量）。

一个遵循WSGI规范的服务器或网关**应该**在文档中描述它们自己的定义的同时，适当地说明下它们可以提供哪些变量。而应用程序这边则**应该**对它们要用到的每一个变量的存在性进行检查，并且在当检测到某些变量不存在时要有备用的措施。

注意: 缺失的变量（比如当没有发生身份验证时的`REMOTE_USER`变量）应该被排除在`environ`字典之外。同样需要注意的是，CGI定义的变量，如果有出现的话，那必须是字符串类型。使用任何除了字符串类型以外的CGI变量都是违反本规范的。

除了CGI定义的变量，`environ`字典也**可以**包含任何操作系统相关的环境变量，并且**必须**包含下面这些WSGI定义的变量：

| 变量                | 变量值                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `wsgi.version`      | 元组`(tuple)` `(1, 0)`，代表WSGI版本 1.0。                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `wsgi.url_scheme`   | 应用程序被调用过程中的一个字符串，表示URL中的`"scheme"`部分。正常情况下，它的值是`"http"`或者`"https"`，视场合而定。                                                                                                                                                                                                                                                                                                                                                                                     |
| `wsgi.input`        | 能读取到HTTP请求主体`(body)`的输入流（类文件对象)。（服务器或网关可以根据应用程序的请求按需读取；也可以预读取客户端的请求主体然后缓存在内存或者磁盘中；又或者根据它们自己的参数利用其他技术来提供这样一种输入流。)                                                                                                                                                                                                                                                                                       |
| `wsgi.errors`       | 用来写错误信息的输出流（类文件对象），以标准化的方式（集中）记录程序的出错信息。它应该是一个“文本模式”的流；举一个例子，应用程序应该用`'\n'`作为行结束符，并且默认服务器/网关能将它转换成正确的行结束符。  对很多服务器来说，`wsgi.errors`是服务器的主要错误日志。当然也有其它选择，比如`sys.stderr`，或者干脆是某种形式的日志文件。服务器的文档应当包含以下这类解释：比如该如何配置这些日志，又或者该从哪里去查找这些记录下来的输出。如果需要，一个服务器或网关还可以向不同的应用程序提供不同的错误流。 |
| `wsgi.multithread`  | 如果一个应用程序对象同时被处于同一个进程中的不同线程调用，则这个参数值应该为`true`，否则就为`false`。                                                                                                                                                                                                                                                                                                                                                                                                    |
| `wsgi.multiprocess` | 如果相同的应用程序对象同时被其他进程调用，则此参数值应该为`true`；否则就为`false`。                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `wsgi.run_once`     | 如果服务器/网关期待（但不保证）应用程序在它所在的进程生命期间只会被调用一次，则这个值应该为`true`。正常情况下，对于那些基于CGI（或类似）的网关，这个值只可能是`true`。                                                                                                                                                                                                                                                                                                                                   |

最后想说的是，这个`environ`字典有可能会包含那些服务器定义的变量。这些变量应该用小写字母，数字，英文句号及下划线来命名，并且应该定义一个服务器/网关专有的前缀开头。举个例子，`mod_python`在定义变量的时候，就会使用类似`mod_python.some_variable`这样的名字。

#### 输入流和错误流 (Input and Error Streams)

服务器提供的输入输出流必须提供以下的方法：

| 方法(Method)      | 流(Stream) | 注释(Notes) |
| ----------------- | ---------- | ----------- |
| `read(size)`      | input      | 1           |
| `readline()`      | input      | 1, 2        |
| `readlines(hint)` | input      | 1, 3        |
| `__iter__()`      | input      |             |
| `flush()`         | errors     | 4           |
| `write(str)`      | errors     |             |
| `writelines(seq)` | errors     |             |
  
除了如下提及的注意事项，以上所有方法的语义在Python Library Reference里已经写得很具体了。

1. 服务器不要读取超过客户端指定的`Content-length`长度的数据，如果应用程序试图读取超出这个长度范围的数据，服务器可以返回一个文件结束符`(end-of-file)`。应用程序**不应该**读取超出`CONTENT_LENGTH`变量指定的长度范围的数据。
2. `readline()`方法不支持可选的`size`参数，因为它会给服务器作者带来额外的复杂性，而且在实际中它不并常用。
3. 请注意，`readlines()`方法中的`hint`参数对于它的调用者和实现者都是可选的。应用程序可以不提供它，服务器或网关这端也可以忽略它。
4. 由于错误流不能回转`(rewound)`，服务器和网关可以直接转发`(forward)`写操作，而不需要进行缓存。在这种情况下，`flush()`方法可能就是个空操作`(no-op)`。不过，具备良好可移植性的应用程序不能假定这个输出流是无缓冲的，也不能假定`flush()`是一个空操作。应用程序必须通过调用`flush()`方法来确保输出写入完成（例如：在多进程下对同一个日志文件的写入操作，主动调用`flush()`可以起到数据混杂最小化的作用）。

所有遵循此规范的服务器都**必须**支持上表中所列出的每一个方法。所有遵循此规范的应用程序都**不能**在输入流和错误流对象上使用除上表之外的其他方法或属性。另外，应用程序也**不能**调用存在的`close()`方法来关闭这些流。

### `start_response()`函数 (The `start_response()` Callable)

传递给应用程序的第二个参数是形如`start_response(status, reponse_headers, exc_info=None)`的可调用对象。（同所有的WSGI可调用对象类似，它的参数必须是位置参数，而非关键字参数）。`start_response`被用来启动一个HTTP响应，它必须返回一个形如`write(body_data)`的可调用对象（具体参考下文的[缓冲和流](#缓冲和流-buffering-and-streaming)章节）

`status`参数是HTTP的`"状态字符串(status)"`，例如：`"200 OK"`, `"404 Not Found"`。它包含一个状态码和一个原因短语，状态码在前，原因短语在后，中间用空格分隔，两端不包含任何其他的字符或空格（详情请参见[RFC 2616](http://tools.ietf.org/html/rfc2616.html)的6.1.1节）。`status`字符串**不能**包含控制字符，末尾也不能有回车换行等其他的组合符号。

`response_headers`参数是`(header_name, header_value)`元组的列表，它必须是一个严格的Python列表类型，既`type(response_headers) is ListType`。如有需要，服务器**可以**随意修改它的内容。每一个`header_name`都必须是合法的HTTP首部`(header)`字段名（在[RFC 2616](http://www.faqs.org/rfcs/rfc2616.html)的4.2节中定义），末尾不能有冒号或其他标点符号。

所有的`header_value`中都**不能**含有包括回车换行在内的任何控制字符，无论是在中间嵌入还是在末尾追加（做这样的要求是为了方便那些必须检查响应头的服务器、网关和中间件，使它们将必需的解析工作复杂度降到最低）。

一般来说，服务器或网关负责确保将正确的HTTP首部`(headers)`发送到客户端，如果应用程序`(application)`遗漏了必要的HTTP首部字段（或其他同等的相关规范结构），则服务器或网关**必须**补全。 比如`HTTP Date:`头和`Server:`头，它们通常是由服务器或网关提供的。

（这里必须给服务器/网关的作者们提个醒: HTTP首部字段`(header)`的名称不区分大小写，因此在检查应用程序提供的首部字段时请务必考虑到这一点！）

应用程序和中间件禁止使用HTTP/1.1的`"逐跳路由(hop-by-hop)"`特性和相应的首部字段`(headers)`，也不能使用HTTP/1.0中的等价特性，和那些可能会对客户端与服务器之间的长连接产生影响的首部字段`(headers)`。这类特性是Web服务器的专属领域，如果一个应用程序尝试发送这类特性，那么服务器或网关**必须**将其看作是一个致命错误，并且从被供给的`start_response()`中抛出异常。（关于`"逐跳路由(hop-by-hop)`特性和首部字段的具体信息，请参阅[HTTP的其他特性](#http的其他特性-other-http-features)章节。)

`start_response`可调用对象**不能**直接发送响应首部。相反地，服务器或网关必须储存它们，并**只有**在对应用程序所返回对象的首次产生非空字符串的迭代过程后，或是应用程序调用`write()`后，才能发送它们。换句话说，响应首部`(headers)`要在响应主体`(body)`真正可用后，或是应用程序返回的对象结束迭代后，才能被发送（唯一可能的例外是，响应首部`(headers)`里带有值为0的`Content-Length`字段）。

响应首部的延迟发送，是为了确保带缓存或异步过程的应用程序，直到最后一刻都能够利用出错信息替换掉它们一开始打算的输出。举个例子，如果应用程序利用缓存生成响应主体的过程出错了，应用程序就需要把原来的`"200 OK"`响应状态字符串`(status)`替换成`"500 Internal Error"`。

如果有提供`exc_info`参数，则它必须是一个Python的`sys.exc_info()`元组`(tuple)`。该参数只有在`start_response`被一个错误处理程序`(error handler)`调用时才需要被提供。如果提供了`exc_info`参数，并且还没有任何HTTP首部被发送，那么`start_response`应当使用新提供的HTTP首部去替换掉当前已存储的HTTP响应首部，从而允许应用程序在错误发生的情况下可以针对输出“改变主意”。

然而，假如提供`exc_info`参数时HTTP首部已经被发送，那么`start_response`**必须**抛出错误，而且这个错误**应该**是`exc_info`元组。即：

```python
raise exc_info[0], exc_info[1], exc_info[2]
```

这样会使应用程序重新捕获该异常，并且原则上应该也会终止应用程序（一旦HTTP首部被发送，应用程序再尝试向浏览器发送错误信息就是不安全的了）。如果应用程序调用`start_response`时传递了`exc_info`参数，那么它**一定不能**捕获任何由`start_response`抛出的异常。相反，应用程序应该允许这些异常传播回服务器或者网关。更多信息请参考下文的[错误处理](#错误处理-error-handling)章节。

应用程序**可能**多次调用`start_response`，当且仅当后续的调用提供`exc_info`参数时。更确切的说，如果`start_response`已经被当前应用程序调用过了，那么在没有提供`exc_info`参数的情况下再次调用`start_response`就是一个严重错误。（请参考上面CGI网关示例来帮助理解准确的逻辑）

注意：实现了`start_response`的服务器、网关和中间件**应该**确保除了在函数调用期间，不持有任何对`exc_info`参数的引用，这样能避免栈帧回溯过程`(traceback and frames involved)`产生循环引用`(circular reference)`。最简单的例子如下：

```python
def start_response(status, response_headers, exc_info=None):
    if exc_info:
         try:
             # 这里处理 w/exc_info
         finally:
             exc_info = None  # 避免循环引用。
```

### 处理`Content-Length`首部 (Handling the `Content-Length` Header)

如果应用程序没有提供`Content-Length`首部，则服务器或网关可以有几种方法来处理它，这些方法当中最简单的就是在响应完成的时候关闭客户端连接。

在某些情况下，服务器或网关能够生成`Content-Length`首部，或至少避免关闭客户端连接。如果应用程序*没有*调用`write()`，且返回的可迭代对象的长度是1`(len() is 1)`，则服务器可以通过可迭代对象生成的第一个字符串的长度来确定`Content-Length`的值。

另外，如果服务器和客户端都支持HTTP/1.1中的`"分块传输编码(chunked encoding)"`[[3]](#reference-3)特性，那么服务器**可以**利用`chunked编码`在每一次调用`write()`方法或迭代生成字符串时后发送一个数据块`(chunk)`，并为每一个数据块生成一个`Content-Length`。这样就可以让服务器保持与客户端的长连接。注意，如果真要这么做，服务器**必须**完全遵循[RFC 2616](http://tools.ietf.org/html/rfc2616.html)规范，否则就应另寻它法。

（注意：应用程序和中间件的输出**一定不能**使用任何类型的传输编码`(Transfer-Encoding)`技术，如`chunking`和`gzipping`，或是`"逐跳路由(hop-by-hop)"`。因为应用传输编码是服务器和网关的职责。详细信息可以参见下文的[HTTP的其他特性](#http的其他特性-other-http-features)章节）

### 缓冲和流 (Buffering and Streaming)

一般而言，应用程序都会选择先缓存（适当大小的）输出再一次性发送的方式来提高吞吐量。这是一种十分常见的做法，Zope等框架都是如此：输出会先被缓存到`StringIO`或类似的对象里面，然后连同响应首部一次性发送出去。  

WSGI中相对应的处理方法是让应用程序简单地返回一个只包含一个元素的可迭代对象`(single-element iterable)`，比如列表`(list)`，它的唯一元素是响应主体`(response body)`的字符串形式。这是一种对于绝大多数应用程序都推荐的工作方式，因为将渲染出来的HTML页面保存到内存中十分容易。

然而，对于大文件或HTTP流服务（比如多部分对象集合`(multipart)`中的`"服务器推送(server push)"`，应用程序往往需要将输出切分为多个较小的块（这样做能够避免将整个大文件加载进内存）。另一种情况是，响应的某些部分的生成过程耗时很长，这时能提前发送该响应体中那些已经生成好的内容就很有必要。

在这些情况下，应用程序一般会返回一个可迭代者（通常是迭代器形式的生成器`(generator-iterator)`），然后逐块`(block-by-block)`地生成最终结果。由于（对于做服务器推送）要插入多部分对象边界`(multipart boundaries)`，或仅仅是做一些耗时长的任务（比如读硬盘上的另一个数据块），这些数据分块的生成可能是间断进行的。

WSGI服务器、网关和中间件**不允许**延迟发送任何数据块，它们**必须**将数据块完整地发送给客户端，或者保证应用程序正在生成下一个数据块的同时它们将继续发送。服务器、网关和中间件可以用下列三种方案中的任意一种来提供该担保：

1. 交还控制权给应用程序前，将整个数据块发送给操作系统（并刷新`(flushed)`O/S缓冲区）；
2. 在应用程序生成下一个块的过程中，使用另一个线程来确保当前数据块能被继续发送；
3. （仅适用于中间件）发送整个数据块到上级服务器或网关。

通过提供这样的保证措施，WSGI就能给应用程序提供这样的抽像：输出数据的过程不会在任意点上陷入停滞。这对于确保诸如多部分对象集合`(multipart)`中的`"服务器推送(server push)"`流服务的正常工作是至关重要的，因为多部分对象边界`(multipart boundaries)`间的数据应当被完整地传送至客户端。

#### 中间件的块边界处理 (Middleware Handling of Block Boundaries)

为了更好地支持异步应用程序和服务器，中间件组件**一定不能**阻塞迭代过程以等待从应用程序的可迭代对象`(iterable)`中返回多个值。如果中间件需要从应用程序中累积更多的数据才能够生成一个输出，那么它**必须**生成`(yield)`一个空字符串。

让我们换一种方式来表述这项要求，每一次当下层的应用程序生成了一个值，中间件组件都必须生成**至少一个**值。如果中间件什么值都生成不了，那么它也**必须**生成一个空字符串。

这项要求确保了异步的服务器和应用程序能共同合作，减少同时运行给定数量的应用程序实例所需的线程数。

需要注意的是，这样的要求也意味着一旦下层的应用程序返回了一个可迭代对象`(iterable)`，中间件就**必须**尽快地返回一个可迭代对象`(iterable)`。另外，中间件也不被允许利用`write()`来传输由下层应用程序生成的数据。中间件仅可以使用它上级服务器的`write()`来发送由下层应用程序使用其提供的`write()`发送来的数据。

#### `write()`函数 (The `write()` Callable)

一些现有框架的APIs与WSGI的一个不同处理方式是它们支持无缓存的输出，特别需要指出的是，它们提供一个`write`函数或方法来写一个无缓冲的块或数据，或者它们提供一个缓冲的`write`函数和一个“刷新（flush）”机制来刷新缓冲。  

不幸的是，就WSGI这样“可迭代”的应用程序返回值来说，除非使用多线程或其他的机制，否则这样的APIs并没有办法实现。

因此为了允许这些框架继续使用这些必要的APIs，WSGI中包含了一个特殊的`write()`调用，它由`start_response`可调用者返回。

如果有办法避免的话，新的WSGI应用程序和框架不应该使用`write()`调用。严格说来，这个`write()`调用是用来支持必要的流APIs的。一般来说，应用程序应该通过返回的可迭代对象`(iterable)`来生成输出，因为这样可以使得web服务器在同一个Python线程中不同任务之间的交织变得可能，整体上来讲是为服务器提供了更好的吞吐量。

这个`write()`调用是由`start_response`可调用者返回的，它接受一个唯一的参数：一个将作为部分HTTP响应体而被写入的字符串，它被看作是已经被迭代生成后的结果。换句话说，在`writer()`返回前，它必须保证传入的字符串要么已经完全发送给客户端，要么已经在应用程序继续处理的过程当中被缓存用做传输了。  

一个应用程序必须返回一个可迭代者对象，即使它使用`write()`来生成全部或部分响应体。返回的可迭代者可以是空的（例如生成一个空字符串），但是，假如它不生成空字符串，那么它的输出就就必须被服务器或者网关正常处理（比如说，它必须立即被发送或者是立即加入到队列当中）。应用程序不能在它们返回的可迭代者内调用`write()`。这样的话，任意一个由可迭代者生成的字符串均会在所有传递给`write()`的字符串都被传送至客户端之后被传送。

### Unicode问题 (Unicode Issues)

HTTP协议不提供对Unicode的直接支持，与此相同，本文档定义的接口也不提供对Unicode的支持。所有的编解码工作都必须在应用程序端来处理，所有传给服务器或从服务器传出的字符串必须是Python的标准字节字符串，而不能是Unicode对象。在要求使用字符串对象的地方使用Unicode对象，将会产生不可预料的结果。

也要注意，作为状态字符串或响应首部传给`start_response()`方法的字符串在编码方面都必须遵循[RFC 2616](http://tools.ietf.org/html/rfc2616.html)规范。也就是说，它们必须使用ISO-8859-1字符集，或者使用[RFC 2047](http://tools.ietf.org/html/rfc2047.html)MIME编码。

有些Python平台的`str`或者`StringType`类型实际上是基于Unicode的（如jython，ironPython，python 3000等），在其上实现本规范时，所有的“字符串”必须只包含以ISO-8859-1编码（从`\u0000`到`\u00FF`）表示的代码点`(code points)`。如果应用程序提供的字符串包含任何其它的 Unicode字符或代码点，将引发生严重错误。同样地，服务器和网关也**不允许**向应用程序提供任何Unicode字符。

再次声明，本规范中提到的所有的字符串都**必须**是`str`或`StringType`类型，不能是`unicode`或`UnicodeType`类型。并且，针对本规范中所提到的作为`"字符串(string)"`的值，即便是一些平台的`str/StringType`对象支持超过8位`(bits)`的字符，也仅有低8位`(bits)`会被用到。

### 错误处理 (Error Handling)

一般来说，应用程序**应该**负责捕获其的内部产生的错误，并且负责向浏览器输出有用的信息（由应用程序自己来决定哪些是“有用”的信息）。

然而，要显示这样的一条信息，并不是说应用程序真的向浏览器发送了数据，而且真这样做的话有损坏响应的风险。因此，WSGI提供了一种机制，允许应用程序发送它自己的错误信息，或是自动地终止应用程序：通过传递`exc_info`参数给`start_response`。这里有个如何使用它的例子：

```python
try:
    # 这里是常规的应用程序代码
    status = "200 Froody"
    response_headers = [("content-type", "text/plain")]
    start_response(status, response_headers)
    return ["正常的程序体（normal body）放这里"]
except:
    # 在这个简陋的‘except:’之前，XXX应该在一个单独的handler里捕捉运行时异常，
    # 譬如 MemoryError，KeyboardInterrupt 这些...
    status = "500 Oops"
    response_headers = [("content-type", "text/plain")]
    start_response(status, response_headers, sys.exc_info())
    return ["这里放程序的错误主体(error body)"]
```

当有异常发生时，如果输出还没有被写入，则对`start_response`的调用将正常返回，然后应用程序会返回一个错误信息主体发送至浏览器。然而如果有部分输出已经被发送到浏览器了，那么`start_response`将会重新抛出预备好的异常。这个异常不应当会被应用程序捕获，因此应用程序会异常终止。服务器和网关会捕获这个（严重）异常并终止响应。  

服务器应当捕获任何使应用程序和其迭代返回过程终止的异常，并记录日志。如果应用程序出错的时候已经有一部分响应被发送给浏览器了，则服务器和网关**可以**尝试添加一个错误消息给到输出，当然，前提是已经发送的首部里有一个标明内容类型为`text/*`字段，让服务器就知道如何正确地做出修改。

一些中间件可能想提供额外的异常处理服务，或者拦截并替换应用程序的出错信息。在这种情况下，中间件可以选择抛出一个替换过的异常而**不是**重新抛出传递给`start_response`的`exc_info`，或者也可以在存储了所提供的参数之后简单地返回而不包含任何异常。这将会让应用程序返回错误主体的可迭代对象`(iterable)`（或调用`write()`），然后让中间件来捕获并修改错误输出。以上这些只有在应用程序的开发者们做到下面这些时才能发挥作用：  

1. 使用`exc_info`发起错误响应；  
2. 当传递`exc_info`参数时，不捕获由`start_response`产生的异常。

### HTTP 1.1 Expect/Continue 机制 (HTTP 1.1 Expect/Continue)

那些实现了HTTP1.1的服务器或网关，必须提供对HTTP1.1中`"Expect/Continue"`机制的透明支持，这可以通过以下几种方式来实现：

1. 对含有`Expect: 100-continue`的的请求直接返回`"100 Continue"`响应，然后正常处理。
2. 正常处理请求，但是提供给应用程序一个特殊的`wsgi.input`流，当/如果应用程序第一次尝试从输入流中读取的时候，就发送一个`"100 Continue"`响应。这个读取请求必须一直阻塞，直到客户端响应请求。  
3. 一直等待，直到客户端确认服务器不支持`expect/continue`特性，然后客户端自己发来请求体。（这个方法较差，不推荐）

注意，以上这些行为的限制不适用于HTTP 1.0请求，也不适用于那些往应用程序对象发送的请求。更多关于HTTP 1.1 Except/Continue的信息，请参阅[RFC 2616](http://tools.ietf.org/html/rfc2616.html)的8.2.3节和10.1.1节。

### HTTP的其他特性 (Other HTTP Features)

通常来说，服务器和网关应当“尽少干涉”，应当让应用程序对它们自己的输出有100%的控制权。服务器/网关只做一些小的改动并且这些小改动不会影响到应用程序响应的语义（semantics ）。应用程序的开发者总是有可能通过添加中间件来额外提供一些特性的，所以服务器/网关的开发者在实现服务器/网关的时候可以适当偏保守些。在某种意义上说，一个服务器应当将自己看作是一个HTTP“网关服务器（gateway server）”，应用程序则应当将自己看作是一个HTTP “源服务器（origin server）”（关于这些术语的定义，请参照 [RFC 2616](http://www.faqs.org/rfcs/rfc2616.html) 的1.3章节）

然而，由于WSGI服务器和应用程序并不是通过HTTP通信的，[RFC 2616](http://www.faqs.org/rfcs/rfc2616.html) 中提到的“逐跳路由（hop-by-hop）”并没有应用到WSGI内部通信中。因此，WSGI应用程序一定不能生成任何"逐跳路由（hop-by-hop）"头信息[[4]](#refrence)，试图使用HTTP中要求它们生成这样的报头的特性，或者依赖任何传入的"逐跳路由（hop-by-hop）"`environ`字典中报头。WSGI服务器必须自己处理所有已经支持的"逐跳路由（hop-by-hop）"头信息，比如为每一个到达的信息做传输解码，解码也要包括那些分块编码（chunked-encoding）的，如果有的话。

如果将这些原则应用到各种各样的HTTP特性中去，应该很容易得知：服务器可以通过`If-None-Match`及`If-Modified-Since`请求头，`Last-Modified`及`ETag`响应头等方式来处理缓存验证。然而，这并不是必须的，如果应用程序自身支持的话，则应用程序应当自己负责处理缓存验证，因为服务器/网关就没有说必须要做这样的验证。

同样地，服务器可能会对一个应用程序的响应做重编码或传输编码，不过，应用程序应当对自己发送的内容做适当的编码并且不能做传输编码。如果客户端请求需要，则服务器可能以字节范围（byte ranges）的方式传送应用程序的响应，应用程序并没有对字节范围（byte ranges）提供原生支持。再次申明，如果有需要，应用程序则应当自己执行此功能。

注意，这些对应用程序的限制不是说要求每一个应用程序都重新实现一次所有的HTTP特性；中间件可以实现许多HTTP特性的全部或者一部分，这样便可以让服务器和应用程序作者从一遍又一遍实现这些特性的痛苦中解放出来。

### 线程支持 (Thread Support)

线程的支持取决于服务器。服务器虽然可以同时并行处理多个请求，但也**应当**提供额外的选择让应用程序可以以单线程的方式运行，这样一来，一些不是线程安全的应用程序或框架也可以在这些服务器上运行。

## 具体实现/应用程序备注 (Implementation/Application Notes)

### 服务器扩展APIs (Server Extension APIs)

一些服务器的作者可能希望暴露更多高级的API，让应用程序和框架的作者能用来做更特别的功能。例如，一个基于`mod_python`的网关可能就希望暴露部分Apache API作为WSGI的扩展。

在最简单的情况下，这只需要定义一个`environ`变量，其它的什么都不需要了，比如`mod_python.some_api`。但是，更多情况下，那些可能出现的中间件会就使情况变得复杂的多。比如，一个API，它提供了访问`environ`变量中出现的同一个HTTP报头的功能，如果`environ`变量被中间件修改，则它很可能会返回不一样的值。

通常情况下，任何重复、取代或者绕过部分WSGI功能的扩展API都会有与中间件组件不兼容的风险。服务器/网关开发者不能寄希望于没人使用中间件，因为有一些框架的作者们明确打算（重新）组织他们的框架，使之几乎完全就像各种中间件一样工作。

所以，为了提供最大的兼容性，提供了扩展API来取代部分WSGI功能的服务器/网关，必须设计这些API以便它们被部分替换过的API调用。例如:一个允许访问HTTP请求头的扩展API需必须要求应用程序传输当前的`environ`，以便服务器/网关可以验证那些能被API访问的HTTP头，验证它们没有被中间件修改过。如果该扩展的API不能保证它总是就HTTP报头内容同`environ`达成协议，它就必须拒绝向应用程序提供服务。例如，通过抛出一个错误，返回None来代替头信息集合，或者其它任何适合该API的东西。

同样地，如果扩展的API额外提供了一种方法来写响应数据或头信息，它应当要求`start_response` 这个可调用者在应用程序能获得的扩展的服务之前被传入。如果传入的对象和最开始服务器/网关提供给应用程序的不一样，则它就不能保证正确运转并且必须拒绝给应用程序提供扩展的服务。

这些指南同样适用于中间件，中间件添加类似解析过的cookies信息，表单变量，会话sessions，或者类似`evniron`。特别地，这样的中间件提供的这些特性应当像操作`environ`的函数那样，而不仅仅是简单地往`evniron`里面填充值。这样有助于保证来自信息是从`evniron`里计算得来的，在所有中间件完成每一个URL重写或对`evniron`做的其它修改之后。

服务器/网关和中间件的开发者们遵守这些“安全扩展”规则是非常重要的，否则以后就可能出现中间件的开发者们为了确保应用程序使用他们扩展的中间件时不被绕过， 而不得不从`environ`中删除一些或者全部的扩展API这样的事情。

### 应用程序配置 (Application Configuration)

这份规范没有定义一个服务器如何选择/获得一个应用程序来调用。因为这和其他一些配置选项一样都是高度取决于服务器的。我们期望那些服务器/网关的作者们能关心并且负责将这些事情文档化：比如如何配置服务器来执行一个特定的应用程序对象，以及需要带什么样的参数（如线程的选项）。

另一方面，Web框架的作者应当关心这些事情并将它们文档化：比如应该怎样创建一个包装了框架功能的应用程序对象。而已经选定了服务器和应用程序框架的用户，必须将这两者连接起来。然而，现在由于Web框架和服务器有了两者之间共同的接口，使得这一切变成了一个机械式的问题，而不再是为了将新的应用程序和服务器配对组合的重大工程了。

最后，一些应用程序，框架，和中间件可能希望使用`evniron`字典来接受一些简单的字符串配置选项。服务器和网关应当通过允许应用程序部署者向`evniron`字典里指定特殊的名-值对（name-value pairs）对来支持这些。最简单的例子是，由于部署者原则上可以配置这些外部的信息到服务器上，或者在CGI的情况下它们可能是通过服务器的配置文件来设置。所以，可以仅仅从`os.environ`中复制操作系统提供的所有环境变量到`environ`字典中就可以了。

应用程序本身应该尽量保持所需要的变量个数最少，因为并不是所有的服务器都支持简单地配置它们。当然，即使在最槽糕的情况下，部署一个应用程序的人还可以通过创建一个脚本来提供一些必要的选项值：

```python
from the_app import application

def new_app(environ, start_response):
    environ['the_app.configval1'] = 'something'
    return application(environ, start_response)
```

但是，大多数现有的应用程序和框架很大可能只需用到`environ`里面的唯一一个配置值，用来指示它们的应用程序或框架特有的配置文件位置（当然，应用程序应当缓存这些配置，以避免每次调用都重复读取）。

### URL的重建 (URL Reconstruction)

如果应用程序希望重建一个请求的完整URL，可以使用下面的算法，该算法由lan Bicking **[译者注：此大神乃pip，virtualenv的作者]** 提供：

```python
from urllib import quote
url = environ['wsgi.url_scheme']+'://'

if environ.get('HTTP_HOST'):
    url += environ['HTTP_HOST']
else:
    url += environ['SERVER_NAME']

    if environ['wsgi.url_scheme'] == 'https':
        if environ['SERVER_PORT'] != '443':
           url += ':' + environ['SERVER_PORT']
    else:
        if environ['SERVER_PORT'] != '80':
           url += ':' + environ['SERVER_PORT']

url += quote(environ.get('SCRIPT_NAME', ''))
url += quote(environ.get('PATH_INFO', ''))
if environ.get('QUERY_STRING'):
    url += '?' + environ['QUERY_STRING']
```

注意，通过这种方式重建出来的URL可能跟客户端真实发过来的URI有些许差别。举个例子，服务器的重写规则有可能会对客户端发来的最初请求的URL做修改，以便让它看起来更规范。

### 对旧版本Python(2.2之前)的支持 (Supporting Older Versions of Python)

有些服务器、网关或者应用程序可能希望对Python2.2之前的版本提供支持。这在目标平台是Jython时甚是如此，因为在我写这篇文档的时候，还没有一个生产版本的Jython 2.2。

对于服务器和网关来说，这是相当容易做到的：准备使用Python 2.2之前的版本的服务器和网关，只需要简单地限定它们自己只使用标准的“for”循环来迭代应用程序返回来的所有可迭代对象`(iterable)`即可。这是能在代码级别确保2.2之前的版本的迭代器协议(后续会讲)跟“现在的”迭代器协议（参照 [PEP234](https://www.python.org/dev/peps/pep-0234/) ）兼容的唯一方法。

（需要注意的是，这个技巧当然只针对那些由Python写的服务器，网关，或者中间件。至于如何正确地在其他语言写的服务器中使用迭代器协议则不在我们这份PEP的讨论范围之内）

不过，对于应用程序这边来说，要提供对Python2.2之前的版本的支持则会稍微复杂些：

- 由于Python 2.2之前，文件并不是可迭代的，故你不能返回一个文件对象并期望它能像一个可迭代者那样工作。（总体来说，你也不能这么做，因为大部分情况下这样做的表现很糟糕）。可以使用`wsgi.file_wrapper`或者一个应用程序特有的文件包装类。（请参考 [可选的平台相关的文件处理](#optional) 章节获取更多关于`sgi.file_wrapper`的信息，该章节包含一个怎么把一个文件包装成一个可迭代者的例子）
- 如果你想返回一个定制加工过的可迭代者，那么它必须实现2.2版本之前的迭代器协议。也就是说，提供一个`__getitem__`方法来接收一个整形的键值，然后在所有数据都取完的时候抛出一个`IndexError`异常。（注意，直接使用内置的序列类型也是可行的，因为它也实现了这个迭代器协议。)

最后，如果中间件也希望对Python2.2之前的版本提供支持，迭代应用程序返回的所有值或者由它自己返回一个可迭代者（又或者是两者都有），那么这些中间件必须遵循以上提到的这些建议。

（另外，为了支持Python2.2之前的版本，毫无疑问，任何服务器，网关，应用程序，或者中间件必须只能使用该版本有的语言特性，比如用1和0，而不是True和False，诸如此类。)

### 可选的平台相关文件处理 (Optional Platform-Specific File Handling)

有些操作环境提供了特殊的高性能文件传输机制，比如Unix下的`sendfile()`方法。服务器和网关可以通过`environ`变量中的 `wsgi.file_wrapper` 这个选项来使用这个机制。应用程序可以使用这样的“文件包装（file wrapper）”来将一个文件或者类文件对象（file-like object ）转换为一个可迭代者然后返回它。例如：

```python
if 'wsgi.file_wrapper' in environ:
    return environ['wsgi.file_wrapper'](filelike, block_size)
else:
    return iter(lambda: filelike.read(block_size), '')
```

如果一个服务器或网关有提供`wsgi.file_wrapper`选项，则它必须是个可调用对象`(callable)`，并且这个可调用者接受一个必要的位置参数，和一个可选的位置参数。第一个参数是将要发送的类文件对象，第二个参数是可选的，表示分块大小（block size）的建议（这个服务器/网关无需使用）。这个可调用者必须返回一个可迭代的对象（iterable object），并且在服务器/网关真正从应用程序那里接收到了一个可迭代者作为返回值之前，不能执行任何的数据传送（否则会阻碍中间件解析或覆盖响应数据（response data））。

至于那个由应用程序提供的被当作是类文件的对象，它则必须拥有一个`read()`方法并接受一个可选的size参数。它可能还需要有一个`close()`方法，如果有，那么由`wsgi.file_wrapper`返回的可迭代者它必须有一个`close()`方法可以调用最初的类文件对象中的`close()`方法。如果这个“类文件“对象还拥有任何的方法或属性与Python内置的文件对象的属性或方法名相同（例如`fileno()`），那么`wsgi.file_warpper`可能会假设这些方法或属性跟Python内置的文件对象的语义（semantics）是相同的。

在真实的实现中，任何平台相关的的文件处理都必须发生在应用程序返回之后，接着服务器/网关会去检查一个包装对象（wrapper object）是否有返回。（再次声明，由于存在中间件，错误处理等等类似的东西，所以并不保证任何生成的包装（wrapper）会被真正地使用到）

除了处理`close()`方法，从语义上讲，应用程序返回一个包装的文件（file wrapper ）应当看起来就像是应用程序返回了一个可迭代者`iter(filelike.read, '')`一样。换句话说，当传输开始的时候，应当从文件的当前位置开始传输，并且继续直到最后完成。

当然，平台相关的文件传输API通常不接受随意的类文件对象，所以，一个`wsgi.file_wrapper`为了判断类文件对象是否适用于支持的平台相关的API，不得不对提供的对象做一些类似`fileno()`（类Unix 平台下）或者是`java.nio.FileChannel`（Jython下）的自省检查。

注意：即使对象不适用与特定的平台API，`wsgi.file_wrapper`必须仍旧返回一个包装了的`read()`和`close()`的迭代，因此应用程序使用这文件包装器便可以再不同平台间移植。这里有个简单的平台无关的文件包装类，适应于旧的（2.2之前）和新的Python，如下：

```python
class FileWrapper:

    def __init__(self, filelike, blksize=8192):
        self.filelike = filelike
        self.blksize = blksize
        if hasattr(filelike, 'close'):
            self.close = filelike.close

    def __getitem__(self, key):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        raise IndexError
```

这里是一段来自服务器/网关的小程序，它提供了访问一个特定平台的API的办法：

```python
environ['wsgi.file_wrapper'] = FileWrapper
result = application(environ, start_response)

try:
    if isinstance(result, FileWrapper):
        # 检查 result.filelike 是否为可用的 w/platform-specific API，
        # 如果是，则使用该API来传送结果。
        # 如果不是，则按正常情况循环处理可迭代者(iterable)。

    for data in result:
        # etc.

finally:
    if hasattr(result, 'close'):
        result.close()
```

## 问答环节 (Questions and Answers)

1. 为什么`evniron`必须是字典？用子类`(subclass)`不行吗？  

   > 用字典是为了最大化地满足在服务器之间的移植性。还有另一种选择就是定义一些字典方法的子集，并以字典的方法作为标准的可移植的接口。实际上，大多数的服务器会使用满足需求的字典，但框架的作者会期待完整的字典特性，因为字典结构一般会实现这些特性。但问题是，如果有一些服务器不使用字典，尽管这类服务器也“符合”规范，还是可能会出现互操作性的问题。因此，强制使用字典可以简化规范并保证互操作性。
   >
   > 注意，以上这些并不妨碍服务器或框架的开发者们向`evnrion`字典里加入自定义的变量来提供特殊的服务。事实上我们鼓励使用这种方式来提供任意的增值服务。

2. 为什么你既可以调用`write()`又可以生成`(yield)`字符串/返回一个可迭代对象`(iterable)`？我们难道不应该只选择一种方式吗？

   > 如果我们仅支持迭代的方法，那么现存的那些假定“推模式`(push)`”的框架就很难实现本规范。但是，如果我们只支持通过`write()`的推模式，那么服务器在做大文件传输这类任务时就会出现性能下降（如果工作线程`(worker)`没有将所有的输出都发送完成，它就无法处理新请求）。因此，我们做这样的妥协，好处是允许应用程序根据实际情况选择这两种方法，并且比起单纯的**push-only**的方式来说，只会给那些服务器的实现者们增加一点点负担而已。

3. `close()`方法是拿来做什么的？

   > 在应用程序执行期间，当写操作`(writes)`完成之后，应用程序可以通过一个`try/finally`代码块来确保资源都被释放了。但是，如果应用程序返回一个可迭代对象`(iterable)`，那么在迭代器被垃圾收集器收集之前任何资源都不会被释放。这里的`close()`惯用法允许应用程序在一个请求完成后释放重要资源，并且向前兼容[PEP 325](https://www.python.org/dev/peps/pep-0325/)里`try/finally`与生成器的用法。

4. 为什么这个接口要设计地这么初级？我希望添加更多酷炫的功能！（比如cookies、会话`(sessions)`、持久性`(persistence)`，等等)

   > 记住，这并不是另一个Python的web框架，这仅仅是一个框架向web服务器通信的方法，反之亦然。如果你想拥有上面所说的这些特性，你需要选一个提供了这些特性的框架。并且如果这个框架让你创建一个WSGI应用程序，你将可以让它跑在大多数支持WSGI的服务器上面。同样的，一些WSGI服务器或许会通过在它们的`environ`字典里提供的对象来提供一些额外的服务；可以参阅这些服务器具体的文档了解详情。（当然，使用这类扩展的应用程序将面临着无法移植到其他基于WSGI的服务器上的风险）

5. 为什么使用CGI的变量而不是旧的HTTP头呢？并且为什么将它们和WSGI定义的变量混在一起呢？  

   > 许多现有的框架很大程度上是建立在CGI规范基础上的，并且现有的web服务器知道如何生成CGI变量。相比之下，使用另一种表示HTTP入站信息的方式只会使市场更加碎片化并降低市场份额。因此使用CGI“标准”看起来是个不错的办法，它能最大化重用已有的实现。如果不将它们同WSGI变量混合在一起，就需要传入两个字典参数，这什么显而易见的好处。

6. 那关于状态字符串，我们可不可以仅仅使用数字来代替，比如说传入“200”而不是“200 OK”？

   > 这样做会使服务器和网关变得复杂化，因为如果这样做的话服务器或网关就需要一个数值状态和相应信息的映射表。相比之下，让应用程序或框架的作者们在他们处理专门的响应代码时顺便输入一些额外的信息则显然要简单地多，并且事实上，经常是现有的框架已经有一个这样的映射表包含这些需要的信息了。总之，权衡之后，我们认为这个让应用程序和框架来负责要比服务器和网关来负责要更适合些。  

7. 为什么`wsgi.run_once`不能保证app仅仅运行一次？

   > 因为它仅仅只是建议应用程序应当“装备妥当但不需要经常性地运行（rig for infrequent running）”。这是因为应用程序框架在操作缓存、会话这些东西的时候有多种模式。在“多重运行（Multiple Run）”模式下，框架可能会预先加载缓存，并且在每个请求之后可能不会有写操作，比如写日志或会话数据到硬盘上等操作。在“单运行（single run）”模式下，框架没有预加载，避免了在每一个请求之后刷新（flush）所有必要的写操作。  
   >
   > 然而，为了验证在后者的模式下应用程序或框架的正确操作，可能会必要地（或是权宜之计）不止一次调用它。因此，一个应用程序不应当仅仅因为设置了`wsgi.run_once`为True就认定它肯定不会被再次运行。

8. 在应用程序代码里使用Feature X（字典`(dictionaries)`，可调用对象`(callables)`等等）这些特性显得很丑陋，难道我们不可以使用对象来代替吗？

   > WSGI中这些所有特性的实现选择都是为了从另外一个特性中解耦合考虑的；将这些特性重新组装到一个封装完好了的对象之中只会在一定程度上增大写服务器/网关的难度，并且在将来希望写一个中间件来只代替/修改一小部分整体功能的时候，难度会上升一个数量级。
   >
   > 本质上，中间件希望有个“职责连”的模式，凭借这个模式它可以在一些功能中被看成是一个“handler”，而同时允许其他功能保持不变。这样的要求，在接口想要保持可扩展性的前提下，用普通的Python对象是比较难实现的。例如，你必须使用`__getattr__`或者`__getattribut__`的重写（override）来确保这些扩展（比如未来的WSGI版本定义的变量）是被通过的。
   >
   > 这种类型的代码是出了名的难以保证100%正确的，并且极少人愿意自己重写。他们倾向于简单地复用别人的实现，可是一旦别人修改了实现的另一处地方时他们却未能及时更新自己的拷贝。  
   >
   > 进一步讲，这种必需的样本代码将是纯碎的消费税，一种纯粹由中间件开发者们承担的开发者消费税，它的目的仅仅是为了能给应用程序框架开发者们支持支持稍微“漂亮”点儿的API而已。但是，应用框架开发者们往往只会更新一个框架来支持WSGI，这只占他们所有框架的非常有限的部分。这很可能是他们的第一个（也可能是唯一一个）WSGI实现，因此他们很有可能去实现这份现成的规范。这样，花时间利用对象的属性或诸如此类的东西让这些API看起来"更漂亮"，对正在读此文的您们来说，可能就是浪费时间。
   >
   > 我们鼓励那些希望在直接的Web应用程序编程（相对于web框架开发）中有更漂亮的（或是改进的）WSGI接口的人，鼓励他们去开发APIs或者框架来包装WSGI，使WSGI对那些应用程序开发者们更加便利。这样的话，WSGI就不仅可以在底层维持对服务器或中间件的便利性，同时对应用程序开发者来说又不会显得太“丑陋”。

## 尚在讨论中的提议 (Proposed/Under Discussion)

下面这些项都还正在Web-SIG或其他地方讨论中，或者说还在PEP作者的计划清单中：

- `wsgi.input`是否改成一个迭代器而不是一个文件？这对于那些异步应用程序和分块编码（ chunked-encoding）的输入流是有帮助的。   
- 我们正在讨论可选的扩展，它们将用来暂停一个应用程序输出的迭代，直到输入可用或者发生一个回调事件。
- 添加一个章节，关于同步 vs 异步应用程序和服务器，相关的线程模型，以及这方面的问题/设计目标。

## 鸣谢 (Acknowledgements)

感谢那些Web-SIG邮件组里面的人，没有他们周全的反馈，将不可能有我这篇修正草案。特别地，我要感谢：   

- `mod_python`的作者Gregory “Grisha” Trubetskoy，是他毫不留情地指出了我的第一版草案没有提供任何比“普通旧版的CGI”有优势的地方，他的批评促进了我去寻找更好的方法。    
- Ian Bicking，是他总是唠叨着要我适当地提供多线程（multithreading）及多进程（multiprocess）相关选项，对了，他还不断纠缠我让我提供一种机制可以让服务器向应用程序提供自定义的扩展数据。  
- Tony Lownds，是他提出了`start_response`函数的概念，提供给它status和headers两个参数然后返回一个write函数。他的这个想法为我后来设计异常处理功能提供了灵感，尤其是在考虑到中间件重写(overrides)应用程序的错误信息这方面。  
- Alan Kennedy, 一个有勇气去尝试实现`WSGI-on-Jython`（在我的这份规范定稿之前）的人，他帮助我形成了 [对Python2.2之前的版本的支持](#对Python2.2之前的版本的支持) 这一章节，以及可选的`wsgi.file_wrapper`套件。  
- Mark Nottingham，是他为这份规范的HTTP RFC 发行规范做了大量的后期校对工作，特别针对HTTP/1.1特性，没有他的指出，我甚至不知道有这东西存在。

## 参考文献 (References)

1. <span id="reference-1">[The Python Wiki "Web Programming" topic](https://wiki.python.org/moin/WebProgramming)</span>

2. <span id="reference-2">[The Common Gateway Interface Specification, v 1.1, 3rd Draft](http://ken.coar.org/cgi/draft-coar-cgi-v11-03.txt)</span>

3. <span id="reference-3">["Chunked Transfer Coding" -- HTTP/1.1, section 3.6.1](http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.6.1)</span>

4. <span id="reference-4">["End-to-end and Hop-by-hop Headers" -- HTTP/1.1, Section 13.5.1](http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html#sec13.5.1)</span>

5. <span id="reference-5">[mod_ssl Reference, "Environment Variables"](http://www.modssl.org/docs/2.8/ssl_reference.html#ToC25)</span>

## 版权 (Copyright)

本文档已发布到[公开区域](https://github.com/python/peps/blob/master/pep-0333.txt)。
