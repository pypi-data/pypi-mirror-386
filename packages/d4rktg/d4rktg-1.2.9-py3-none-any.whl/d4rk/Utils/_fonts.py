# src/Utils/_fonts.py

import re

__font1 = {'a' : 'ᴀ','b' : 'ʙ','c' : 'ᴄ','d' : 'ᴅ','e' : 'ᴇ','f' : 'ғ','g' : 'ɢ','h' : 'ʜ','i' : 'ɪ','j' : 'ᴊ','k' : 'ᴋ','l' : 'ʟ','m' : 'ᴍ','n' : 'ɴ','o' : 'ᴏ','p' : 'ᴘ','q' : 'ǫ','r' : 'ʀ','s' : 's','t' : 'ᴛ','u' : 'ᴜ','v' : 'ᴠ','w' : 'ᴡ','x' : 'x','y' : 'ʏ','z' : 'ᴢ','1' : '𝟷','2' : '𝟸','3' : '𝟹','4' : '𝟺','5' : '𝟻','6' : '𝟼','7' : '𝟽','8' : '𝟾','9' : '𝟿','0' : '𝟶'}
__font2 = {'a':'𝐚','b':'𝐛','c':'𝐜','d':'𝐝','e':'𝐞','f':'𝐟','g':'𝐠','h':'𝐡','i':'𝐢','j':'𝐣','k':'𝐤','l':'𝐥','m':'𝐦','n':'𝐧','o':'𝐨','p':'𝐩','q':'𝐪','r':'𝐫','s':'𝐬','t':'𝐭','u':'𝐮','v':'𝐯','w':'𝐰','x':'𝐱','y':'𝐲','z':'𝐳','1':'𝟏','2':'𝟐','3':'𝟑','4':'𝟒','5':'𝟓','6':'𝟔','7':'𝟕','8':'𝟖','9':'𝟗','0':'𝟎'}
__font3 = {'a':'𝒶','b':'𝒷','c':'𝒸','d':'𝒹','e':'ℯ','f':'𝒻','g':'𝑔','h':'𝒽','i':'𝒾','j':'𝒿','k':'𝓀','l':'𝓁','m':'𝓂','n':'𝓃','o':'𝑜','p':'𝓅','q':'𝓆','r':'𝓇','s':'𝓈','t':'𝓉','u':'𝓊','v':'𝓋','w':'𝓌','x':'𝓍','y':'𝓎','z':'𝓏','1':'𝟣','2':'𝟤','3':'𝟥','4':'𝟦','5':'𝟧','6':'𝟨','7':'𝟩','8':'𝟪','9':'𝟫','0':'𝟢'}
__font4 = {'a':'𝓐','b':'𝓑','c':'𝓒','d':'𝓓','e':'𝓔','f':'𝓕','g':'𝓖','h':'𝓗','i':'𝓘','j':'𝓙','k':'𝓚','l':'𝓛','m':'𝓜','n':'𝓝','o':'𝓞','p':'𝓟','q':'𝓠','r':'𝓡','s':'𝓢','t':'𝓣','u':'𝓤','v':'𝓥','w':'𝓦','x':'𝓧','y':'𝓨','z':'𝓩','1':'𝟙','2':'𝟚','3':'𝟛','4':'𝟜','5':'𝟝','6':'𝟞','7':'𝟟','8':'𝟠','9':'𝟡','0':'𝟘'}
__font5 = {'a':'🅰','b':'🅱','c':'🅲','d':'🅳','e':'🅴','f':'🅵','g':'🅶','h':'🅷','i':'🅸','j':'🅹','k':'🅺','l':'🅻','m':'🅼','n':'🅽','o':'🅾','p':'🅿','q':'🆀','r':'🆁','s':'🆂','t':'🆃','u':'🆄','v':'🆅','w':'🆆','x':'🆇','y':'🆈','z':'🆉','1':'➊','2':'➋','3':'➌','4':'➍','5':'➎','6':'➏','7':'➐','8':'➑','9':'➒','0':'⓿'}
__font6 = {'a':'𝕒','b':'𝕓','c':'𝕔','d':'𝕕','e':'𝕖','f':'𝕗','g':'𝕘','h':'𝕙','i':'𝕚','j':'𝕛','k':'𝕜','l':'𝕝','m':'𝕞','n':'𝕟','o':'𝕠','p':'𝕡','q':'𝕢','r':'𝕣','s':'𝕤','t':'𝕥','u':'𝕦','v':'𝕧','w':'𝕨','x':'𝕩','y':'𝕪','z':'𝕫','1':'𝟙','2':'𝟚','3':'𝟛','4':'𝟜','5':'𝟝','6':'𝟞','7':'𝟟','8':'𝟠','9':'𝟡','0':'𝟘'}


def get_font(text: str, font: int = 1):
    if int(font) ==0:return text
    font_name = f"__font{font}"
    font_style: dict = globals().get(font_name, None)
    if not text:
        return text
    if font_style is None:
        return text 
    
    def convert(match):
        if match.group("tag"):
            return match.group("tag")  # Preserve HTML tags
        elif match.group("braced"):
            return match.group("braced")  # Preserve {placeholders}
        elif match.group("command"):
            return match.group("command")  # Preserve /commands
        elif match.group("mention"):
            return match.group("mention") 
        else:
            content = match.group("text")
            return "".join(font_style.get(char, char) for char in content)

    pattern = (
        r"(?P<tag><[^>]+>)"        # HTML tags
        r"|(?P<braced>\{[^}]+\})"  # Braced placeholders
        r"|(?P<command>/\w+)"      # /commands
        r"|(?P<mention>@[\w_]+)"   # @usernames (mentions)
        r"|(?P<text>\w+)"          # Regular words
    )

    return re.sub(pattern, convert, text.lower(), flags=re.IGNORECASE)



