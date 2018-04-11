<!DOCTYPE html>
<html>
<head>
<title>Meu Blog com Python e MongoDB</title>
</head>
<body>

%if (username != None):
Welcome {{username}}        <a href="/logout">Logout</a> | <a href="/newpost">New Post</a> | <a href="/welcome">Home</a><p>
%end

<h1>Categorias</h1>

<p>Categorias já cadastradas</p>
<ul>
    %for cat in categories:
        <li>
            {{ cat["category"] }}
            <form style="display: inline;"  action="/remove_category" method="post">
                <input type="hidden" name="category_id" value="{{ cat['_id'] }}">
                <button style="display: inline;" type="submit">X</button>
            </form>
        </li>
    %end
</ul>

<h1>Criar Categoria</h1>


<form action="/create_category" method="post">
    <label>Categoria
        <input type="text" name="category">
    </label>
    <button type="submit">Salvar</button>
</form>


</body>
</html>