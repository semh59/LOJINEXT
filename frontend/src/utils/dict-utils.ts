/**
 * Deep merge/patch utility for JSON objects.
 * get_dict_diff çıktısını frontend'de mevcut state'e uygulamak için kullanılır.
 */
export function applyPatch<T extends Record<string, any>>(base: T, patch: any): T {
    if (!patch || typeof patch !== 'object' || Array.isArray(patch)) {
        return patch as T;
    }

    const result: any = { ...base };

    for (const key in patch) {
        if (Object.prototype.hasOwnProperty.call(patch, key)) {
            const patchValue = (patch as any)[key];
            const baseValue = result[key];

            if (
                patchValue &&
                typeof patchValue === 'object' &&
                !Array.isArray(patchValue) &&
                baseValue &&
                typeof baseValue === 'object' &&
                !Array.isArray(baseValue)
            ) {
                // Her iki taraf da objeyse recursive birleştir
                result[key] = applyPatch(baseValue, patchValue);
            } else {
                // Değilse doğrudan üzerine yaz
                result[key] = patchValue;
            }
        }
    }

    return result;
}
