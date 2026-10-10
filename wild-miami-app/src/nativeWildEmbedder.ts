export type LoadModelResult = { loadMs: number; source: 'bundled' | 'provisioned' };

export type WildEmbedder = {
  loadModel(expectedSha256: string): Promise<LoadModelResult>;
  embedImage(photoUri: string): Promise<number[]>;
  embedText(text: string): Promise<number[]>;
};

export const PINNED_MODEL_SHA256 = '92dcbea108899e5d6e30d919b0744f90d9967e80c67a4ab5503ac16d54f62eb0';

export async function loadNativeModelIfAvailable(): Promise<LoadModelResult> {
  // Placeholder for the Kotlin Expo module. Keep this explicit so the UI never
  // silently pretends fixture mode is real ML.
  throw new Error('Native WildEmbedder module is not installed yet; running in Demo/FIXTURE mode.');
}
