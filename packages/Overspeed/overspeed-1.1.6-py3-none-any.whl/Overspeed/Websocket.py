from . import Library , Const;
from .Function import Function;
from .Control import Control;

class Websocket :
    
    @classmethod
    def Lunch(Self , Context:Library.Simple) -> None :
        Context.Signal = Library.Simple(
            Proctitle = f'{Context.Config.Proctitle}.Websocket' ,
            Config = Context.Config.Websocket ,
            Handle = Self.Client ,
        );
        Control.Lunch(Context);
    
    @classmethod
    async def Client(Self , Context:Library.Simple , Reader:Library.Asyncio.StreamReader , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            while True :
                Context = await Control.Request(Context , Reader);
                if Context.Signal.Request.Status is False : break;
                if len(Context.Signal.Request.Header) == 0 : raise ValueError(402);
                if Context.Signal.Request.Header.get('upgrade' , str()).lower() == 'websocket' : await Self.Upgrade(Context , Reader , Writer);
        except ValueError as Error :
            try :
                Context.Signal.Response = dict(Code = Error.args[0]);
                await Self.Send(Context , Writer);
            except : Function.Trace(Context.Journal);
        except : Function.Trace(Context.Journal);
    
    @classmethod
    async def Upgrade(Self , Context:Library.Simple , Reader:Library.Asyncio.StreamReader , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            if Writer.is_closing() is False :
                Writer.write(Const.Socket_Upgrade % (
                    Function.Hash(f'{Context.Signal.Request.Header.get("sec-websocket-key")}{Const.Socket_Guid}').encode() ,
                ));
                await Writer.drain();
                await Self.Session(Context , Reader , Writer);
        except : Function.Trace(Context.Journal);
        finally : await Library.Asyncio.sleep(0);
    
    @classmethod
    async def Session(Self , Context:Library.Simple , Reader:Library.Asyncio.StreamReader , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            Context.Begin = Function.Time(Int = False);
            Queue = Library.Asyncio.Queue();
            Active = Library.Weakref.WeakSet();
            Event = Library.Asyncio.Event();
            Waiting = Library.Asyncio.create_task(Self.Worker(Queue , Context.Journal , Writer , Active , Event));
            while not Event.is_set() or not Writer.is_closing() :
                if (Function.Time(Int = False) - Context.Begin) > Context.Signal.Config.Connect : break;
                if Context.Signal.Config.Timeout > 0 :
                    try : Header = await Library.Asyncio.wait_for(Reader.readexactly(2) , timeout = Context.Signal.Config.Timeout);
                    except : break;
                else : Header = await Reader.readexactly(2);
                Fin = Header[0] & Const.Socket_Fin;
                Opcode = Header[0] & Const.Socket_Opcode;
                Masked = Header[1] & Const.Socket_Fin;
                Payload = Header[1] & Const.Socket_Payload;
                if Payload == 126 : Payload = Library.Struct.unpack(Const.Socket_H , await Reader.readexactly(2))[0];
                if Payload == 127 : Payload = Library.Struct.unpack(Const.Socket_Q , await Reader.readexactly(8))[0];
                Mask = await Reader.readexactly(4) if Masked else Const.Socket_Empty;
                Load = await Reader.readexactly(Payload);
                if Masked : Load = bytes(Byte ^ Mask[Index % 4] for Index , Byte in enumerate(Load));
                if Opcode in (1 , 2) :
                    Context.Signal.Uuid = Function.Uuid();
                    try : Context.Signal.Request.Body = Library.Json.loads(Load);
                    except :
                        Body = Load.decode();
                        Parse = Library.Parse.parse_qs(Body);
                        if len(Parse) == 0 : Context.Signal.Request.Body = Body;
                        else : Context.Signal.Request.Body = Function.Parse(Body);
                    finally :
                        if 'Header' in Context.Signal.Request.Body :
                            Context.Signal.Request.Header.update(Context.Signal.Request.Body.get('Header'));
                            Context.Signal.Request.Body.pop('Header' , None);
                        if Context.Signal.Config.Journal is True : Context.Journal.put(Library.Simple(
                            Method = 'Websocket' ,
                            Type = 'Request' ,
                            Body = Context.Signal ,
                        ));
                        await Queue.put(Library.Copy.deepcopy(Context.Signal));
                else : break;
            await Queue.put(None);
            await Waiting;
        except ValueError as Error :
            try :
                Context.Signal.Response = dict(Code = Error.args[0]);
                await Self.Send(Context , Writer);
            except : Function.Trace(Context.Journal);
        except : Function.Trace(Context.Journal);
        finally : await Library.Asyncio.sleep(0);
    
    @classmethod
    async def Worker(Self , Queue:Library.Asyncio.Queue , Journal:Library.Processing.Queue , Writer:Library.Asyncio.StreamWriter , Active:set , Event:Library.Asyncio.Event) -> None :
        while not Event.is_set() or not Writer.is_closing() :
            Context = await Queue.get();
            if Context is None : break;
            Task = Library.Asyncio.create_task(Self.Task(Library.Simple(
                Signal = Context ,
                Journal = Journal ,
            ) , Writer));
            Active.add(Task);
            Task.add_done_callback(lambda T : Active.discard(T));
    
    @classmethod
    async def Task(Self , Context:Library.Simple , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            Response = await Library.Asyncio.to_thread(Control.Business , Context);
            if type(Response.get('Body')) is Library.Types.GeneratorType :
                for Generator in Response.get('Body') :
                    if Generator is None : break;
                    Context.Signal.Response = Generator;
                    await Self.Send(Context , Writer);
            else :
                Context.Signal.Response = Response;
                await Self.Send(Context , Writer);
        except :
            try :
                Context.Signal.Response = dict(Code = 503);
                await Self.Send(Context , Writer);
            except : pass;
            finally : Function.Trace(Context.Journal);
    
    @staticmethod
    async def Send(Context:Library.Simple , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            if Writer.is_closing() is False :
                Code = Context.Signal.Response.get('Code' , 200);
                Body = Context.Signal.Response.get('Body' , str());
                Close = Context.Signal.Response.get('Close' , False);
                Response_Code = getattr(Const , f'Socket_{Code}' , Const.Socket_400);
                if not Code == 200 and (Body == '' or Body is None or len(Body) == 0) : Body = Response_Code;
                if Body is None : Body = Const.Socket_Empty.decode();
                if isinstance(Body , bytes) is True : Body = Body.decode();
                Data = Library.Json.dumps(dict(
                    Code = Code ,
                    Body = Body ,
                ));
                Header = bytearray();
                Header.append(0x81);
                Length = len(Data);
                if Length <= 125 : Header.append(Length);
                elif Length < 65535 :
                    Header.append(126);
                    Header += Library.Struct.pack(Const.Socket_H , Length);
                else :
                    Header.append(127);
                    Header += Library.Struct.pack(Const.Socket_Q , Length);
                Writer.write(Header + Data);
                await Writer.drain();
                if Context.Signal.Config.Journal is True : Context.Journal.put(Library.Simple(
                    Method = 'Websocket' ,
                    Type = 'Response' ,
                    Body = Context.Signal ,
                ));
                if Close == True : await Control.Close(Writer);
        except : Function.Trace(Context.Journal);
        finally : await Library.Asyncio.sleep(0);
    