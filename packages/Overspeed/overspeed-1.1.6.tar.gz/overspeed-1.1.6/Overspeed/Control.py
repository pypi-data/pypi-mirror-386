from . import Library , Const;
from .Function import Function;

class Control :
    
    @classmethod
    def Lunch(Self , Context:Library.Simple) -> None :
        Function.Proctitle(Context.Signal.Proctitle);
        Process = [Library.Processing.Process(target = Self.Server , args = (Context , Port)) for Port in Context.Signal.Config.Port];
        for X in Process : X.start();
        for X in Process : X.join();
    
    @classmethod
    def Server(Self , Context:Library.Simple , Port:int) -> None :
        Function.Proctitle(f'{Context.Signal.Proctitle}.Server');
        Socket = Library.Socket.socket(Library.Socket.AF_INET , Library.Socket.SOCK_STREAM);
        Socket.setsockopt(Library.Socket.SOL_SOCKET , Library.Socket.SO_REUSEADDR , 1);
        try : Socket.setsockopt(Library.Socket.SOL_SOCKET , Library.Socket.SO_REUSEPORT , 1);
        except : pass;
        Socket.setsockopt(Library.Socket.IPPROTO_TCP , Library.Socket.TCP_NODELAY , 1);
        Socket.setsockopt(Library.Socket.SOL_SOCKET , Library.Socket.SO_SNDBUF , 1 << 20);
        Socket.setsockopt(Library.Socket.SOL_SOCKET , Library.Socket.SO_RCVBUF , 1 << 20);
        Socket.bind((Const.Socket_Host , Port));
        Socket.listen(Const.Socket_Listen);
        Socket.setblocking(False);
        if Library.Platform.system().lower() == 'linux' :
            Process = [Library.Processing.Process(target = Self.Worker , args = (Context , Socket) , daemon = True) for _ in range(Context.Signal.Config.Cpu * Library.Os.cpu_count())];
            for X in Process : X.start();
            for X in Process : X.join();
        else : Self.Worker(Context , Socket);
    
    @classmethod
    def Worker(Self , Context:Library.Simple , Socket:Library.Socket.socket) -> None :
        Function.Proctitle(f'{Context.Signal.Proctitle}.Worker');
        Function.Policy();
        Function.Print(f'{Context.Signal.Proctitle} Start Up, Listen In | Pid[{Library.Os.getpid()}] | Port[{Socket.getsockname()[1]}]');
        Library.Asyncio.run(Self.Running(Context , Socket));
    
    @classmethod
    async def Running(Self , Context:Library.Simple , Socket:Library.Socket.socket) -> None :
        Service = await Library.Asyncio.start_server(
            Library.Functools.partial(Self.Handle , Context) ,
            sock = Socket ,
            reuse_port = True ,
            backlog = Const.Socket_Listen ,
            ssl = Function.Ssl(Context.Signal.Config , Context.Config.Root.Path) ,
        );
        async with Service : await Service.serve_forever();
    
    @classmethod
    async def Handle(Self , Context:Library.Simple , Reader:Library.Asyncio.StreamReader , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            Socket = Writer.get_extra_info('socket');
            Context.Signal.Socket = Socket.fileno();
            Context.Signal.Server = Library.Os.getppid();
            Context.Signal.Worker = Library.Os.getpid();
            Context.Signal.Location = list(Socket.getsockname());
            Context.Signal.Remote = list(Socket.getpeername());
            await Context.Signal.Handle(Context , Reader , Writer);
        except : Function.Trace(Context.Journal);
        finally :
            try : await Self.Close(Writer);
            except : pass;
            finally : await Library.Asyncio.sleep(0);
    
    @staticmethod
    async def Close(Writer:Library.Asyncio.StreamWriter) -> None :
        if Writer.is_closing() is False :
            Writer.close();
            await Writer.wait_closed();
        await Library.Asyncio.sleep(0);
    
    @staticmethod
    async def Request(Context , Reader:Library.Asyncio.StreamReader) -> Library.Simple :
        try :
            Context.Signal.Uuid = Function.Uuid();
            Context.Signal.Request = Library.Simple();
            Context.Signal.Request.Status = False;
            Context.Signal.Request.Method = str();
            Context.Signal.Request.Url = str();
            Context.Signal.Request.Path = str();
            Context.Signal.Request.Cors = False;
            Context.Signal.Request.Original = Const.Socket_Empty;
            Context.Signal.Request.Query = dict();
            Context.Signal.Request.Header = dict();
            Context.Signal.Request.Body = dict();
            Context.Signal.Response = dict();
            try : Head = await Reader.readline();
            except : raise;
            Context.Signal.Request.Original += Head;
            Decode = Head.decode(errors = 'ignore').strip();
            try : Context.Signal.Request.Method , Context.Signal.Request.Url , _ = Decode.split();
            except : raise;
            while True :
                try :
                    try : Header = await Library.Asyncio.wait_for(Reader.readline() , timeout = Const.Socket_Waittime);
                    except : raise;
                    if Header in (Const.Socket_Empty , Const.Socket_Newline) : raise;
                    Context.Signal.Request.Original += Header;
                    Decode = Header.decode(errors = 'ignore').strip();
                    if ':' not in Decode : continue;
                    Primary , Data = Decode.split(':' , 1);
                    if Primary.lower() == 'cookie' :
                        Cookie = Library.Cookie();
                        Cookie.load(Data);
                        Context.Signal.Request.Header['cookie'] = {Key.lower().strip() : Value.value.strip() for Key , Value in Cookie.items()};
                    else : Context.Signal.Request.Header[Primary.lower().strip()] = Data.strip();
                except : break;
            if 'origin' in Context.Signal.Request.Header : Context.Signal.Request.Cors = True;
            Parse = Library.Parse.urlparse(Context.Signal.Request.Url);
            Context.Signal.Request.Path = Parse.path;
            Context.Signal.Request.Query = Function.Parse(Parse.query);
            Context.Signal.Request.Length = int(Context.Signal.Request.Header.get('content-length' , 0));
            if not Context.Signal.Request.Length == 0 and Context.Signal.Request.Method == 'POST' :
                try : Body = await Library.Asyncio.wait_for(Reader.readexactly(Context.Signal.Request.Length) , timeout = Const.Socket_Waittime);
                except : raise;
                Context.Signal.Request.Original += Const.Socket_Newline + Body;
                try : Context.Signal.Request.Body = Library.Json.loads(Body);
                except :
                    Data = Body.decode();
                    Parse = Library.Parse.parse_qs(Data);
                    if len(Parse) == 0 : Context.Signal.Request.Body = Data;
                    else : Context.Signal.Request.Body = Function.Parse(Data);
            Context.Signal.Request.Status = True;
        except : pass;
        finally : return Context;
    
    @staticmethod
    def Business(Context:Library.Simple) -> dict :
        Source = dict(
            Code = 200 ,
            Body = str() ,
            Type = Const.Socket_Html ,
        );
        if Context.Signal.Config.Callable is None : Source['Code'] = 404;
        else :
            Response = Context.Signal.Config.Callable(Library.Simple(
                Remote = Context.Signal.Remote ,
                Location = Context.Signal.Location ,
                Request = Context.Signal.Request ,
            ));
            if isinstance(Response , dict) is True and ('Code' in Response or 'Body' in Response or 'Type' in Response or 'Close' in Response or 'Time' in Response) : Source.update(Response);
            else : Source['Body'] = Response;
        return Source;