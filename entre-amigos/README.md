# ENTRE AMIGOS (2024) | V1 para Windows

**Estado em 11/11/2026:** renderizador e testes sintéticos no GitHub; o filme completo ainda **não** foi renderizado com as mídias originais. A branch main permanece intacta.

## Prévia de revisão de aproximadamente 22 minutos (montagem atual)

**Prioridade 11/11/2026:** gerar e assistir à montagem já programada, sem acrescentar clipes novos nem tentar alcançar 40 minutos. O MP4 ainda **não foi exportado nesta sessão** porque os dois blocos publicados pelo Descript não puderam ser materializados no ambiente de renderização e há referências a originais sem localização confirmada no Drive.

**Iniciador correto: [MONTAR_PREVIA_22MIN_WINDOWS.bat](MONTAR_PREVIA_22MIN_WINDOWS.bat)**

1. Extrair o ZIP desta branch e instalar Python 3.12+ e FFmpeg.
2. Baixar **Bloco 01** (2min43s) do [Descript](https://share.descript.com/view/7aTMx3UqC9x) e salvar como `entre-amigos/blocos/BLOCO_01.mp4`.
3. Baixar **Bloco 02** (1min11s) do [Descript](https://share.descript.com/view/WNgRx7FydqK) e salvar como `entre-amigos/blocos/BLOCO_02.mp4`.
4. Garantir que os vídeos/fotos/músicas originais do Google Drive estejam disponíveis offline no Windows, sem renomear arquivos.
5. Abrir **MONTAR_PREVIA_22MIN_WINDOWS.bat** e informar a pasta original quando solicitado. O BAT verifica antes se cada arquivo do manifesto está disponível e se os blocos têm áudio/vídeo.
6. Caso todos os arquivos estejam disponíveis, o FFmpeg renderiza os trechos por cena, retoma cortes validamente concluídos e executa uma **decodificação de conferência completa** antes de criar `saida/ENTRE_AMIGOS_V1_PREVIA_22MIN.mp4`.
7. Se faltar algum original, a montagem não começa e o programa exibe os nomes exatos. **Não substitua os originais por fotos congeladas nem altere o manifesto para ignorar as faltas.** Se não chegar a 22 minutos, o programa informa a duração real, sem esticar cenas.

Na verificação desta sessão, **dois originais inicialmente ausentes do ambiente foram localizados no Drive** (`20240319_102858.mp4` em `07 - A classificar` e `20240321_111011.jpg` em `05 - Fotografias`). Onze referências não foram localizadas nas pastas consultadas: `20240319_103416.mp4`, `20240508_100654.mp4`, `20240508_100858.mp4`, `20240626_085312.mp4`, `20240702_075048.mp4`, `20240702_082633.mp4`, `20240702_093406.mp4`, `20240702_112156.mp4`, `20240930_104038.mp4`, `20240930_104230.mp4` e `20241101_085645.mp4`. Esses arquivos **podem estar em outras cópias locais**; o preflight do Windows fará a verificação definitiva. Não escolher substitutos sem assistir.

## Material anterior preservado

- [Bloco 01, 2min43,7s, com abertura aprovada incluída](https://share.descript.com/view/7aTMx3UqC9x)
- [Bloco 02, 1min11,3s, C09 a C12](https://share.descript.com/view/WNgRx7FydqK)
- [Abertura isolada como referência, não reinserir](https://drive.google.com/file/d/1ljz6cSW9yFi836xtZ8p_XWULkv3O6kZU/view)
- [Edição original no Descript](https://web.descript.com/bb1c9a8d-d468-48e4-9e8b-18494dbf9871)

## Windows, sem programação

1. [Baixar ZIP desta branch](https://github.com/PainD14/oficina-git-base/archive/refs/heads/entre-amigos-v1-recuperacao.zip). Extrair e abrir a pasta **entre-amigos**.
2. Instalar [Python 3.12+](https://www.python.org/downloads/windows/) e FFmpeg. No PowerShell: **winget install --id Gyan.FFmpeg --exact**. Reabrir o terminal se necessário.
3. Baixar os dois MP4 do Descript. Colocar na subpasta **blocos**, com os nomes exatos **BLOCO_01.mp4** e **BLOCO_02.mp4**.
4. Disponibilizar offline a pasta principal do documentário através do Google Drive para computador. Preservar subpastas, vídeos, fotos e músicas originais, sem renomear.
5. Dar dois cliques no **MONTAR_V1_WINDOWS.bat**. Colar o caminho da pasta das mídias quando solicitado. Ele verifica Python, FFmpeg, bibliotecas e todos os arquivos de fonte antes de iniciar.
6. Acompanhar o progresso por cena no terminal. Saída prevista: **entre-amigos/saida/ENTRE_AMIGOS_V1_REVISAO.mp4**. Duração medida e pendências ficam em **saida/RESULTADO.json** e **saida/PROGRESSO.json**.

Se interromper, execute novamente o mesmo BAT. Segmentos válidos são reaproveitados somente quando os timecodes, músicas e fontes não foram alterados. A pasta **saida** preserva o progresso e os intermediários.

## Estrutura

- **projeto_v1.json**: as 33 cenas e os 97 cortes candidatos, sendo 8 novos intervalos de 5 originais; músicas e caminhos lógicos. C01 inclui todo o Bloco 01, C09 todo o Bloco 02. C10 é um complemento musical após o Bloco 02, não um trecho duplicado.
- **montar_v1.py**: codifica para 1920×1080, 24 fps, H.264/AAC estéreo; mantém áudios originais em entrevistas; aplica músicas a cenas visuais; junta blocos com checagens e cache por assinatura.
- **requirements.txt**: Pillow e pillow-heif para JPG/HEIC.
- **GERAR_PROXIES_GRANDES_WINDOWS.bat** e **gerar_proxies.py**: criar proxies 720p com áudio dos 20 arquivos grandes sem alterar originais. Os proxies servem para decupagem, e o filme deve usar os originais.
- **teste_proxies.py**: teste sintético da geração de proxy com som, duração e integridade do original.
- **teste_tecnico.py**: testes sintéticos com FFmpeg, mixagem, foto vertical, vídeo sem áudio, concatenação e invalidação de cache.
- **.github/workflows/entre-amigos-validar.yml**: testes Linux com FFmpeg.
- **.github/workflows/entre-amigos-windows.yml**: testa o BAT em Windows com dados sintéticos.

A estimativa superior da seleção atual, somando limites dos cortes e durações dos blocos, é de **aproximadamente 22,2 minutos (22min12s)**, não 40. Essa estimativa não é a duração final medida. Para expandir, é preciso escolher mais intervalos IN/OUT pelo conteúdo verdadeiro do vídeo, não somente pela data do arquivo. O programa não estica fotos, não repete material e não inventa falas.

### Ampliação efetivamente selecionada, 11/11/2026

Foram adicionados **8 cortes candidatos, +197,4 segundos (3min17s)**, em cinco originais distintos. Os vídeos foram obtidos sem alterações do Drive; foram gerados quadros visuais amostrados em 16 posições e processado o áudio original por ASR de modo preliminar, **não substituindo escuta humana integral**. Cada corte consta em JSON com IN/OUT, conteúdo visual observado, áudio original e status de verificação. **Não há legendas novas**.

| Destino | Arquivo original | IN–OUT (s) | Duração | Conteúdo visual observado |
| --- | --- | --- | ---: | --- |
| Após Bloco 01 (C08) | 20240222_081040.mp4 | 11.20–27.50 | 16,30s | Colega conversando para câmera em sala |
| Após Bloco 01 (C08) | 20240222_081040.mp4 | 29.00–36.50 | 7,50s | Outro colega falando à câmera |
| Após Bloco 01 (C08) | 20240222_115619.mp4 | 00.30–26.00 | 25,70s | Grupo conversando e reagindo em sala |
| Após Bloco 01 (C08) | 20240222_115619.mp4 | 48.30–54.00 | 5,70s | Um colega falando; parte com orientação virada excluída |
| Após Bloco 02 (C12) | 20240321_111033.mp4 | 15.80–80.50 | 64,70s | Entrevista contínua: estudante falando sobre futuro e perspectivas, transcrição exata pendente |
| Após Bloco 02 (C12) | 20240322_085226.mp4 | 01.50–14.00 | 12,50s | Colegas conversando e se apresentando |
| Após Bloco 02 (C12) | 20240322_085226.mp4 | 19.00–40.00 | 21,00s | Reações e conversa de grupo |
| C17, sala de aula | 20240618_090004.mp4 | 09.00–53.00 | 44,00s | Colegas sentados e em pé interagindo em sala |

C08_COMPLEMENTO é colocado **após o Bloco 01 completo**; C12_COMPLEMENTO, **após o Bloco 02 completo**. Os dois blocos editados continuam integrais. Isso mantém 33 capítulos, sem inserir uma C34.

**Faltam cerca de 17min48s de material adicional genuíno**, a ser escolhido por conteúdo, não duração. As melhores fontes a revisar são conversas integrais de abril a julho, o passeio de agosto, outubro e dezembro. Não afirmar que 40 minutos já estão sustentados.

### Como analisar os 20 vídeos grandes

A conexão do Drive bloqueia a transferência de vídeos acima de 256 MiB. No computador Windows, instale Python e FFmpeg, deixe os arquivos disponíveis offline e execute **GERAR_PROXIES_GRANDES_WINDOWS.bat**. Cole o caminho original do Drive. A ferramenta procura a lista das vinte gravações, gera cópias leves em **proxies_para_decupagem**, preserva áudio e timecodes, valida duração e permite retomada após falha. **Os proxies são apenas para revisão; nenhuma tomada de arquivo grande foi incluída sem verificação de conteúdo.**

### Extras revisadas, não extras automáticas

A seleção de tomadas extras apenas pela data foi desativada. O BAT padrão não usa extras. A opção --extras só aceita um arquivo opcional chamado **selecoes_adicionais_aprovadas.json**, com objeto cenas, cada corte com arquivo, entrada, saida, audio, status definido como conteudo_conferido e revisado como true. Essa entrada exige verificação visual e do áudio original. Sem esse arquivo, a opção retorna erro, sem acrescentar filmagens não examinadas.

### Diagnóstico sem editar

No PowerShell, dentro da pasta entre-amigos:

    py -3 montar_v1.py --midias "G:\Meu Drive\ENTRE AMIGOS" --blocos ".\blocos" --verificar

### Executar diretamente

    py -3 montar_v1.py --midias "G:\Meu Drive\ENTRE AMIGOS" --blocos ".\blocos"

Uma renderização incompleta não é apresentada como V1 final. Para exportar uma prévia parcial intencionalmente, o parâmetro --permitir-incompleto gera **ENTRE_AMIGOS_V1_PARCIAL.mp4**, explicitamente identificado.

**Pendências editoriais:** C27 pode conter leitura de mensagem alheia e C29 exige verificação do áudio literal. Cortes marcados corte_proposto_revisar ainda precisam de avaliação. Música comercial em distribuição pública exige direitos. Nenhum arquivo original foi publicado no GitHub.
