import type { Method } from 'axios';

export interface ICollectionMeta {
  total: number;
  offset: number;
  limit: number;
}

export interface ICollection<T> {
  meta: ICollectionMeta;
  items: T[];
}

export interface IConstraint {
  name: string;
  message: string;
}

export interface IResponseError {
  path: string;
  property: string;
  constraints: IConstraint[];
}

export interface IBackendResponse<D = unknown> {
  status: number;
  message: string;
  data: D;
  errors: IResponseError[];
}

export interface IResponse<D = unknown> {
  ok: boolean;
  code: number;
  message: string;
  data: D;
  errors: IResponseError[];
}

export interface IContractPrototype {
  url: string;
  method: Method;
  data: unknown;
  params: unknown;
  response: unknown;
}

export interface IContract<C extends IContractPrototype> {
  url: C['url'];
  method: C['method'];
  data: C['data'];
  params: C['params'];
  response: C['response'];
}

export type PR<C extends IContractPrototype> = Promise<IResponse<C['response']>>;
