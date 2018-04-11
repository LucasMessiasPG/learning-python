<!doctype HTML> 
<html 
<head>
   <title> 
      Blog Post 
   </title>
</head>
<body>
    %if (username != None):
      Welcome {{username}}        <a href="/logout">Logout</a> | <a href="/newpost">New Post</a> | <a href="/welcome">Home</a><p>
    %end
   <a href="/">Blog Home</a><br><br> 
   <h2>{{post['title']}}</h2>
   %if ('category' in post):
      Category: <a href="/category/{{ post['category'] }}">{{ post['category'] }}</a><br>
    %end
   Posted {{post['date']}}<i> By {{post['author']}}</i><br>
   <hr>
   {{!post['body']}} 
   <p> 
      <em>Filed Under</em>: 
      %if ('tags' in post): 
        %for tag in post['tags'][0:1]: 
            <a href="/tag/{{tag}}">{{tag}}</a> 
            %for tag in post['tags'][1:]: 
                , <a href="/tag/{{tag}}">{{tag}}</a> 
            %end 
        %end 
      %end 
    </p>
    <h3>Add a comment</h3> 
    <form action="/newcomment" method="POST"> 
        <input type="hidden" name="permalink", value="{{post['permalink']}}"> 
        {{errors}} 
        <b>Nome</b> (obrigatorio)<br> 
        <input type="text" name="commentName" size="60" value="{{comment['name']}}"><br> 
        <b>Email</b> (opcional)<br> 
        <input type="text" name="commentEmail" size="60" value="{{comment['email']}}"><br> 
        <b>Comentario</b><br> 
        <textarea name="commentBody" cols="60" rows="10">{{comment['body']}}</textarea><br> 
        <input type="submit" value="Submit"> 
    </form>
    <ul>
      %if ('comments' in post): 
        %numComments = len(post['comments']) 
      %else: 
        %numComments = 0 
      %end 
      %for i in range(0, numComments): 
        Author: {{post['comments'][i]['author']}}<br> 
        {{post['comments'][i]['body']}}<br> 
        <hr>
      %end 
   </ul>
</body>
</html>