# Configuração de cookies para YouTube

O download de áudio do YouTube usa a branch SABR do yt-dlp com **cookies da sua conta**. Sem cookies válidos, o download falha com 403 ou erros de SABR.

## Como exportar cookies

1. **Use uma janela anônima/incógnito** (importante: cookies normais rotacionam e param de funcionar).

2. Na janela anônima, acesse `https://www.youtube.com/robots.txt` (deixe esta aba aberta).

3. Abra **outra** janela anônima e faça login no YouTube.

4. Use uma extensão para exportar cookies (ex: "Get cookies.txt" no Chrome/Firefox).

5. Exporte **apenas** os cookies de `youtube.com` no formato Netscape.

6. Salve como `cookies.txt` na pasta `backend/`:
   ```
   backend/cookies.txt
   ```

7. Feche as janelas anônimas **sem** abrir o YouTube nelas de novo (senão os cookies rotacionam).

## Quando os cookies param de funcionar

O YouTube rotaciona cookies por segurança. Se começar a dar erro (403, "cookies inválidos"), exporte novamente seguindo os passos acima.

## Referência

- [yt-dlp: Exporting YouTube cookies](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)
