/**
 * Deep merge/patch utility for JSON objects.
 * get_dict_diff çıktısını frontend'de mevcut state'e uygulamak için kullanılır.
 */
export function applyPatch<T extends Record<string, unknown>>(base: T, patch: Partial<T> | Record<string, unknown>): T {
    if (!patch || typeof patch !== 'object' || Array.isArray(patch)) {
        return patch as T;
    }

    const result: T = { ...base };

    for (const key in patch) {
        if (Object.prototype.hasOwnProperty.call(patch, key)) {
            const patchValue = (patch as Record<string, unknown>)[key];
            const baseValue = (result as Record<string, unknown>)[key];

            if (
                patchValue &&
                typeof patchValue === 'object' &&
                !Array.isArray(patchValue) &&
                baseValue &&
                typeof baseValue === 'object' &&
                !Array.isArray(baseValue)
            ) {
                // Her iki taraf da objeyse recursive birleştir
                (result as Record<string, unknown>)[key] = applyPatch(
                    baseValue as Record<string, unknown>, 
                    patchValue as Record<string, unknown>
                );
            } else {
                // Değilse doğrudan üzerine yaz
                (result as Record<string, unknown>)[key] = patchValue;
            }
        }
    }

    return result;
}
