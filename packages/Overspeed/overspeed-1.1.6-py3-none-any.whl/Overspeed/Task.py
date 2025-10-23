from . import Library;
from .Function import Function;

class Task :
    
    @classmethod
    def Lunch(Self , Context:Library.Simple) -> None :
        Function.Proctitle(f'{Context.Config.Proctitle}.Task');
        if Context.Config.Task.Callable is not None : Context.Config.Task.Callable(Context);