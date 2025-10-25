# Decisões Técnicas - Peepomap

## Flexibilização de Tipos em Métodos de Manipulação

**Data:** 2025-10-24

### Decisão
Os métodos `truncate`, `shift` e `adjust` foram modificados para aceitar tanto strings quanto objetos `LinearSegmentedColormap`.

### Motivação
Melhorar a usabilidade da API permitindo que usuários passem diretamente objetos de colormap criados dinamicamente, sem precisar registrá-los primeiro.

### Implementação
Todos os três métodos agora usam o padrão:
```python
def method_name(
    name: str | LinearSegmentedColormap,
    ...
) -> LinearSegmentedColormap:
    if isinstance(name, str):
        cmap = get(name)
        original_name = name
    else:
        cmap = name
        original_name = getattr(name, "name", "custom")
```

### Testes
Adicionados testes para verificar o comportamento com objetos:
- `test_truncate_by_object()`
- `test_shift_by_object()`
- `test_adjust_by_object()`

---

## Refatoração da Função `concat()`

**Data:** 2025-10-24

### Decisão
A função `concat()` foi completamente refatorada para simplificar a API e tornar o comportamento mais previsível.

### Problema Anterior
A implementação antiga tinha múltiplos problemas:
1. Comportamento diferente para 2 vs 3+ colormaps
2. Parâmetros `center` e `diffusion` confusos e não-intuitivos
3. Transições sempre presentes (mesmo quando não desejadas)
4. Tamanho de transição fixo (10% hardcoded)

### Nova API
```python
def concat(
    *colormaps: str | LinearSegmentedColormap,
    blend: float | None = None,
    n: int = 256,
    reverse: bool = False,
    name: str | None = None,
) -> LinearSegmentedColormap
```

### Comportamento
- **`blend=None`** (padrão): Concatenação direta com espaço igual para cada colormap, sem transições
- **`blend>0.0`**: Interpolação linear suave entre colormaps adjacentes
- **`blend`**: Controla a fração do espaço total usada para blending (0.0-0.5)

### Exemplo
```python
# Sem blending - fronteiras nítidas
cmap = peepomap.concat("viridis", "plasma", "inferno")

# Com blending - 10% do espaço total para transições
cmap = peepomap.concat("viridis", "plasma", blend=0.1)
```

### Correção Crítica
O cálculo de blend foi corrigido para aplicar a fração ao espaço TOTAL e dividir entre as transições, não aplicar por transição:
```python
# Correto
total_blend_requested = int(n * blend)
blend_zone_size = total_blend_requested // n_transitions

# Errado (versão antiga)
blend_zone_size = int(n * blend)  # Aplicado a CADA transição
```

---

## Renomeação de `diffusion` para `blend`

**Data:** 2025-10-24

### Decisão
O parâmetro `diffusion` em `create_diverging()` foi renomeado para `blend` para manter consistência com `concat()`.

### Motivação
Usar terminologia consistente em toda a API. O termo "blend" é mais intuitivo e amplamente usado em ferramentas de visualização.

### Arquivos Modificados
- `src/peepomap/tools.py`: Parâmetro e referências internas
- `tests/test_tools.py`: Nome do teste atualizado
- `README.md`: Exemplos atualizados

---

## Adição de `export()`

**Data:** 2025-10-24

### Decisão
Criada função utilitária para exportar colormaps como objetos `ColormapInfo`, prontos para adição ao registro de colormaps.

### Motivação
Facilitar a persistência de colormaps criados dinamicamente e sua adição ao registro de colormaps do peepomap. A função retorna um objeto `ColormapInfo` (não uma string), consistente com a estrutura de `_COLORMAPS_DATA` em `colormaps.py`.

### API
```python
def export(
    cmap: LinearSegmentedColormap,
    n: int = 32,
    *,
    name: str | None = None,
    cmap_type: ColormapType = "sequential",
    description: str = "",
    output_file: str | None = None,
) -> ColormapInfo
```

### Uso
```python
import peepomap

# Criar colormap customizado
custom = peepomap.create_diverging("Blues_r", "Reds", blend=0.3)

# Exportar como ColormapInfo
info = peepomap.export(
    custom,
    name="custom_div",
    n=32,
    cmap_type="diverging",
    description="Blue to red diverging colormap"
)

# O objeto pode ser usado diretamente
print(info.name)
print(info.colors)

# Ou salvar código Python para colormaps.py
peepomap.export(
    custom,
    name="custom_div",
    cmap_type="diverging",
    description="Blue to red diverging colormap",
    output_file="colormap.py"
)
```

### Implementação
A função:
1. Amostra o colormap em `n` pontos (default 32)
2. Converte array NumPy para lista de listas Python
3. Cria objeto `ColormapInfo` com os parâmetros fornecidos
4. Opcionalmente salva código Python formatado em arquivo
5. Retorna o objeto `ColormapInfo`

### Tipos
A função aceita:
- `cmap_type`: Literal["sequential", "diverging", "cyclic", "multi-diverging"]
- `description`: String descritiva do colormap

### Exportação
A função foi adicionada aos exports públicos em:
- `src/peepomap/tools.py`: `__all__`
- `src/peepomap/__init__.py`: imports e `__all__`

---

## Atualização de Exemplos no README

**Data:** 2025-10-24

### Decisão
Atualizar todos os exemplos no README.md para refletir os exemplos usados em `__main__.py`.

### Mudanças
1. **Concat examples**: Alterado de `create_diverging` para `create_linear` (linha 121-123)
   - Antes: `div1 = peepomap.create_diverging("Blues_r", "Reds", blend=0.3, name="div1")`
   - Depois: `div1 = peepomap.create_linear("blue", "red", name="div1")`

2. **Blend values**: Atualizado para corresponder a __main__.py
   - Concat demo: `blend=0.25` (era 0.1)
   - Concat odd demo: `blend=0.25` (era 0.1)

3. **Complex concat example**: Adicionado novo exemplo com 7 colormaps
   - Demonstra concatenação de múltiplos colormaps com `blend=0.45`

4. **Export colormap section**: Adicionada nova seção documentando `export()`
   - Mostra como exportar colormaps customizados
   - Documenta retorno de `ColormapInfo`
   - Exemplo de salvar em arquivo

### Correção de Bug
- Corrigido key "tria" → "Tria" em `colormaps.py` para consistência
  - O dicionário usava key "tria" mas o campo name era "Tria"
  - Causava erro KeyError nos testes
  - Todos os outros colormaps usam key e name consistentes
