import { z } from 'zod';

/**
 * Ids are prefixed strings generated in the app, not ObjectIds, so a thread or an
 * answer is readable in a log line and in a URL (PRD 8).
 */
const prefixed = (prefix: string, label: string) =>
  z
    .string()
    .regex(new RegExp(`^${prefix}_[A-Za-z0-9_-]+$`), `${label} must look like ${prefix}_…`);

export const ThreadId = prefixed('thr', 'threadId');
export const AnswerId = prefixed('ans', 'answerId');
export const SpaceId = prefixed('spc', 'spaceId');
export const DocId = prefixed('doc', 'docId');
export const ArtifactId = prefixed('art', 'artifactId');
export const RequestId = z.string().min(1);
export const MemoryId = z.string().min(1);
export const UserId = z.string().min(1);

export type ThreadId = z.infer<typeof ThreadId>;
export type AnswerId = z.infer<typeof AnswerId>;
export type SpaceId = z.infer<typeof SpaceId>;
export type DocId = z.infer<typeof DocId>;
export type ArtifactId = z.infer<typeof ArtifactId>;

/** Short, url-safe, collision-resistant enough for one cohort. `newId('thr')` → `thr_k3f9a2b1c7`. */
export function newId(prefix: 'thr' | 'ans' | 'spc' | 'doc' | 'art' | 'req' | 'mem'): string {
  const rand = Math.random().toString(36).slice(2, 8);
  return `${prefix}_${Date.now().toString(36)}${rand}`;
}
