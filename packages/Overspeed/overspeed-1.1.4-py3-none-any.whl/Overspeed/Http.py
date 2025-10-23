from . import Library , Const;
from .Function import Function;
from .Control import Control;

class Http :
    
    @classmethod
    def Lunch(Self , Context:Library.Simple) -> None :
        Context.Signal = Library.Simple(
            Proctitle = f'{Context.Config.Proctitle}.Http' ,
            Config = Context.Config.Http ,
            Handle = Self.Client ,
        );
        Control.Lunch(Context);
    
    @classmethod
    async def Client(Self , Context:Library.Simple , Reader:Library.Asyncio.StreamReader , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            Queue = Library.Asyncio.Queue();
            Waiting = Library.Asyncio.create_task(Self.Worker(Queue , Context.Journal , Writer));
            while True :
                Context = await Control.Request(Context , Reader);
                if Context.Signal.Request.Status is False : break;
                if Context.Signal.Config.Journal is True : Context.Journal.put(Library.Simple(
                    Method = 'Http' ,
                    Type = 'Request' ,
                    Body = Library.Copy.deepcopy(Context.Signal) ,
                ));
                if len(Context.Signal.Request.Header) == 0 : raise ValueError(402);
                if Context.Signal.Request.Length > Context.Signal.Config.Large : raise ValueError(413);
                if Context.Signal.Request.Method == 'OPTIONS' : raise ValueError(204);
                await Queue.put(Library.Copy.deepcopy(Context.Signal));
            
            print(123)
            await Queue.put(None);
            await Waiting;
        except ValueError as Error :
            try :
                Context.Signal.Response = dict(Code = Error.args[0]);
                await Self.Response(Context , Writer);
            except : Function.Trace(Context.Journal);
        except : Function.Trace(Context.Journal);
        finally : await Library.Asyncio.sleep(0);
    
    @classmethod
    async def Worker(Self , Queue:Library.Asyncio.Queue , Journal:Library.Processing.Queue , Writer:Library.Asyncio.StreamWriter) -> None :
        while True :
            Context = await Queue.get();
            if Context is None : break;
            Library.Asyncio.create_task(Self.Task(Library.Simple(
                Signal = Context ,
                Journal = Journal ,
            ) , Writer));
    
    @classmethod
    async def Task(Self , Context:Library.Simple , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            Response = await Library.Asyncio.to_thread(Control.Business , Context);
            if type(Response.get('Body')) is Library.Types.GeneratorType :
                Context.Signal.Response = dict(Type = Const.Socket_Stream , Stream = True);
                await Self.Response(Context , Writer);
                for Generator in Response.get('Body') :
                    if Generator is None : break;
                    Writer.write(f'data:{Library.Json.dumps(Generator)}\n\n'.encode());
                    await Writer.drain();
            else :
                Context.Signal.Response = Response;
                await Self.Response(Context , Writer);
        except :
            try :
                Context.Signal.Response = dict(Code = 503);
                await Self.Response(Context , Writer);
            except : pass;
            finally : Function.Trace(Context.Journal);
    
    @staticmethod
    async def Response(Context:Library.Simple , Writer:Library.Asyncio.StreamWriter) -> None :
        try :
            if Writer.is_closing() is False :
                Code = Context.Signal.Response.get('Code' , 200);
                Type = Context.Signal.Response.get('Type' , str());
                Body = Context.Signal.Response.get('Body' , str());
                Stream = Context.Signal.Response.get('Stream' , False);
                Response_Code = getattr(Const , f'Socket_{Code}' , Const.Socket_400);
                if not Code == 200 and (Body == '' or Body is None or len(Body) == 0) : Body = Response_Code;
                if Body is None : Body = Const.Socket_Empty;
                if isinstance(Body , int) is True or isinstance(Body , float) is True : Body = str(Body);
                elif isinstance(Body , bytes) is False : Body = Library.Json.dumps(Body);
                if isinstance(Body , str) is True : Body = Body.encode();
                if Type == '' or Type is None :
                    Accept = Context.Signal.Request.Header.get('content-type' , Context.Signal.Request.Header.get('accept' , Const.Socket_Html));
                    if Const.Socket_Image is Accept : Response_Type = Const.Socket_Image;
                    elif Const.Socket_Plain is Accept : Response_Type = Const.Socket_Plain;
                    elif Const.Socket_Xml is Accept : Response_Type = Const.Socket_Xml;
                    elif Const.Socket_Json is Accept : Response_Type = Const.Socket_Json;
                    elif Const.Socket_Stream is Accept : Response_Type = Const.Socket_Stream;
                    elif Const.Socket_Data is Accept : Response_Type = Const.Socket_Data;
                    elif Const.Socket_Javascript is Accept : Response_Type = Const.Socket_Javascript;
                    elif Const.Socket_Url is Accept : Response_Type = Const.Socket_Url;
                    else : Response_Type = Const.Socket_Html;
                elif isinstance(Type , bytes) is False : Response_Type = Type.encode();
                else : Response_Type = Type;
                if Stream is True : Writer.write(Const.Socket_Event % (
                    Response_Code ,
                    Response_Type ,
                    Const.Socket_Keep ,
                    Const.Socket_Cors if Context.Signal.Request.Cors is True else Const.Socket_Empty ,
                    Body ,
                ));
                else : Writer.write(Const.Socket_Response % (
                    Response_Code ,
                    Response_Type ,
                    len(Body) ,
                    Const.Socket_Keep ,
                    Const.Socket_Cors if Context.Signal.Request.Cors is True else Const.Socket_Empty ,
                    Body ,
                ));
                await Writer.drain();
                if Context.Signal.Config.Journal is True : Context.Journal.put(Library.Simple(
                    Method = 'Http' ,
                    Type = 'Response' ,
                    Body = Context.Signal ,
                ));
        except : Function.Trace(Context.Journal);
        finally : await Library.Asyncio.sleep(0);