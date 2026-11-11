# ENTRE AMIGOS (2024) | V1 para Windows

**Estado em 11/11/2026:** renderizador e testes sintéticos no GitHub; o filme completo ainda **não** foi renderizado com as mídias originais. A branch main permanece intacta.

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

- **projeto_v1.json**: as 33 cenas e os 89 cortes candidatos; músicas e caminhos lógicos. C01 inclui todo o Bloco 01, C09 todo o Bloco 02. C10 é um complemento musical após o Bloco 02, não um trecho duplicado.
- **montar_v1.py**: codifica para 1920×1080, 24 fps, H.264/AAC estéreo; mantém áudios originais em entrevistas; aplica músicas a cenas visuais; junta blocos com checagens e cache por assinatura.
- **requirements.txt**: Pillow e pillow-heif para JPG/HEIC.
- **teste_tecnico.py**: testes sintéticos com FFmpeg, mixagem, foto vertical, vídeo sem áudio, concatenação e invalidação de cache.
- **.github/workflows/entre-amigos-validar.yml**: testes Linux com FFmpeg.
- **.github/workflows/entre-amigos-windows.yml**: testa o BAT em Windows com dados sintéticos.

A estimativa superior da seleção atual, somando limites dos cortes e durações dos blocos, é de **aproximadamente 18,9 minutos**, não 40. Essa estimativa não é a duração final medida. Para expandir, é preciso escolher mais intervalos IN/OUT pelo conteúdo verdadeiro do vídeo, não somente pela data do arquivo. O programa não estica fotos, não repete material e não inventa falas.

### Extras revisadas, não extras automáticas

A seleção de tomadas extras apenas pela data foi desativada. O BAT padrão não usa extras. A opção --extras só aceita um arquivo opcional chamado **selecoes_adicionais_aprovadas.json**, com objeto cenas, cada corte com arquivo, entrada, saida, audio, status definido como conteudo_conferido e revisado como true. Essa entrada exige verificação visual e do áudio original. Sem esse arquivo, a opção retorna erro, sem acrescentar filmagens não examinadas.

### Diagnóstico sem editar

No PowerShell, dentro da pasta entre-amigos:

    py -3 montar_v1.py --midias "G:\Meu Drive\ENTRE AMIGOS" --blocos ".\blocos" --verificar

### Executar diretamente

    py -3 montar_v1.py --midias "G:\Meu Drive\ENTRE AMIGOS" --blocos ".\blocos"

Uma renderização incompleta não é apresentada como V1 final. Para exportar uma prévia parcial intencionalmente, o parâmetro --permitir-incompleto gera **ENTRE_AMIGOS_V1_PARCIAL.mp4**, explicitamente identificado.

**Pendências editoriais:** C27 pode conter leitura de mensagem alheia e C29 exige verificação do áudio literal. Cortes marcados corte_proposto_revisar ainda precisam de avaliação. Música comercial em distribuição pública exige direitos. Nenhum arquivo original foi publicado no GitHub.
