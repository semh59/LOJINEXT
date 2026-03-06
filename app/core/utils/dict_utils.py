from typing import Any, Dict


def get_dict_diff(old_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    İki sözlük arasındaki farkları hesaplar.
    Yalnızca değişen veya yeni eklenen alanları döndürür.
    Nested (iç içe) sözlükleri de destekler.
    """
    diff = {}

    for key, value in new_dict.items():
        if key not in old_dict:
            diff[key] = value
        elif old_dict[key] != value:
            if isinstance(value, dict) and isinstance(old_dict.get(key), dict):
                nested_diff = get_dict_diff(old_dict[key], value)
                if nested_diff:
                    diff[key] = nested_diff
            else:
                diff[key] = value

    return diff


def apply_dict_patch(
    base_dict: Dict[str, Any], patch: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Bir sözlüğe patch (yama) uygular.
    get_dict_diff çıktısını geri birleştirmek için kullanılır.
    """
    result = base_dict.copy()

    for key, value in patch.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = apply_dict_patch(result[key], value)
        else:
            result[key] = value

    return result
