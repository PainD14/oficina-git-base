# ENTRE AMIGOS | Projeto de recuperação para Windows

**Estado:** manifesto e renderizador salvos em branch separada. O arquivo MP4 final ainda **não foi gerado nem testado** aqui. A execução local anterior ficou indisponível. **Esta branch foi criada agora para recuperação**, não é prova de um projeto antigo localizado no GitHub.

Repositório: https://github.com/PainD14/oficina-git-base
Branch: \`entre-amigos-v1-recuperacao\`
Pasta: \`entre-amigos/\`
Não foram enviados vídeos privados ao GitHub nem alterada a branch \`main\`.

## O que foi preservado

- **Bloco 01**: https://share.descript.com/view/7aTMx3UqC9x , 2min43,7s, com a abertura original de 14,27s **já incluída**.
- **Bloco 02**: https://share.descript.com/view/WNgRx7FydqK , 1min11,3s, cenas C09 a C12.
- **Abertura isolada**: https://drive.google.com/file/d/1ljz6cSW9yFi836xtZ8p_XWULkv3O6kZU/view
- **Projeto editável no Descript**: https://web.descript.com/bb1c9a8d-d468-48e4-9e8b-18494dbf9871

O renderizador usa **Bloco 01 + Bloco 02 uma única vez**, evitando duplicação da abertura e das primeiras 12 cenas.

## Como executar no Windows

1. [Baixe o ZIP desta branch](https://github.com/PainD14/oficina-git-base/archive/refs/heads/entre-amigos-v1-recuperacao.zip), descompacte-o e abra a subpasta **entre-amigos**.
2. Instale **Python 3.12+** e **FFmpeg**. No PowerShell, você pode usar \`winget install --id Gyan.FFmpeg --exact\`. Confirme \`ffmpeg -version\`, \`ffprobe -version\` e \`py -3 --version\` numa nova janela.
3. No Descript, use o botão de download das duas versões publicadas. Salve-as exatamente como \`entre-amigos\blocos\BLOCO_01.mp4\` e \`entre-amigos\blocos\BLOCO_02.mp4\`. **Não baixe a abertura isolada para substituir o Bloco 01**, pois ela já faz parte desse bloco.
4. Instale **Google Drive para computador** e disponibilize a pasta principal do documentário inteiramente no disco. Ela deve conter os vídeos originais em suas subpastas, as fotografias e a pasta de músicas. Não é necessário renomear nada.
5. Dê duplo clique em **MONTAR_V1_WINDOWS.bat**. Cole o caminho local da pasta do documentário quando solicitado.
6. O BAT primeiro verifica as dependências e fontes, depois produz os blocos das cenas e junta os arquivos. O resultado previsto é \`saida\ENTRE_AMIGOS_V1_REVISAO.mp4\`. Consulte \`saida\PROGRESSO.json\` e \`saida\RESULTADO.json\` para saber o que realmente foi feito.

**Para continuar após falha:** execute o mesmo BAT novamente. Clipes e cenas já finalizados são reutilizados. Não apague \`saida\segmentos\` nem \`saida\cenas\` se desejar continuar.

### Teste de disponibilidade, sem renderizar

\`\`\`powershell
py -3 -m pip install -r requirements.txt
py -3 montar_v1.py --midias "G:\Meu Drive\ENTRE AMIGOS" --blocos ".\blocos" --verificar
\`\`\`

### Renderização sem extras (somente seleção documentada)

\`\`\`powershell
py -3 montar_v1.py --midias "G:\Meu Drive\ENTRE AMIGOS" --blocos ".\blocos"
\`\`\`

### Renderização com materiais extras não repetidos

\`\`\`powershell
py -3 montar_v1.py --midias "G:\Meu Drive\ENTRE AMIGOS" --blocos ".\blocos" --extras
\`\`\`

O BAT usa \`--extras\`: acrescenta planos reais não repetidos de acordo com a **data do nome do arquivo**, mantendo **áudio silenciado** nos clipes extras. Não identifica personagens, não cria falas nem legendas, e não alonga cenas artificialmente. Essa seleção é **provisória** e exige avaliação depois de renderizada. Para incluir também clipes gigantes acima de 256 MiB nas tomadas extras, inclua \`--incluir-grandes\` conscientemente.

## Estrutura e dependências

- \`projeto_v1.json\`: 33 cenas (C01–C33), fontes/caminhos lógicos, músicas e janelas de cortes documentadas.
- \`montar_v1.py\`: renderizador Python 3, que chama \`ffprobe\` e \`ffmpeg\`, padroniza clipes e concatena por cena com retomada automática.
- \`requirements.txt\`: Pillow e pillow-heif (JPG/HEIC e créditos).
- \`MONTAR_V1_WINDOWS.bat\`: instalador/checker/launcher.
- \`blocos/\`: você deposita os **dois MP4** já exportados do Descript.
- \`saida/\`: segmentos intermediários, progresso e MP4 gerados pelo script.

**Requisitos:** Python 3.12+, FFmpeg com \`libx264\` e \`aac\`, \`ffprobe\`, Pillow e pillow-heif, espaço livre em disco para originais e intermediários. Os áudios e originais NÃO estão no GitHub.

## Limitações que permanecem

- A montagem completa **não foi renderizada nesta sessão** e não há duração final verificada. A meta de 40 minutos não é garantida: a duração resultará da quantidade real de material disponível, sem preencher tempo.
- As janelas de entrevistas são **candidatas de decupagem**, sujeitas à escuta e à revisão do corte; os trechos de apoio sem tempo final são **propostas**, não quadros verificados.
- A seleção automática de extras por data pode incluir planos fracos ou bastidores. **Revise a V1** antes de considerá-la final.
- Os 20 arquivos muito grandes não estão exigidos por padrão; o arquivo \`1000434736.mp4\` permanece excluído.
- A cópia para a pasta 08 do Drive depende da execução no Windows ou envio manual, já que a conexão atual não transferiu os MP4 publicados.
- A publicação fora de uso privado depende dos direitos musicais.

Para refazer uma cena após alterar \`projeto_v1.json\`, remova \`saida\cenas\Cxx.mp4\` e os respectivos \`saida\segmentos\Cxx_*.mp4\` antes de executar novamente, preservando as demais cenas.
