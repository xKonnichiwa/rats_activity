import axios, { HttpStatusCode } from 'axios';

import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
} from 'axios';
import type { IBackendResponse, PR, IContractPrototype } from './types';


export class Http {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      // withCredentials: true,
    });
  }

  public async baseRequest(
    config: AxiosRequestConfig<unknown>
  ): Promise<AxiosResponse<unknown, unknown>> {
    return await this.client.request(config);
  }

  public async request<C extends IContractPrototype>(
    url: C['url'],
    data: C['data'],
    params: C['params'],
    axiosParams?: AxiosRequestConfig,
    method: C['method'] = 'get'
  ): PR<C> {
    try {
      const response = await this.client.request<
        IBackendResponse<C['response']>,
        AxiosResponse<IBackendResponse<C['response']>>
      >({
        ...axiosParams,
        url,
        data,
        params,
        method,
      });

      if (response.status === HttpStatusCode.Ok) {
        return {
          ok: true,
          code: response.status,
          message: response.data.message,
          data: response.data.data ?? response.data,
          errors: response.data.errors,
        };
      }

      return {
        ok: false,
        code: response.status,
        message: response.data.message,
        data: response.data.data,
        errors: response.data.errors,
      };
    } catch (e) {
      if (axios.isAxiosError<IBackendResponse>(e)) {
        if (typeof e.response !== 'undefined') {
          return {
            ok: false,
            code: e.response.status,
            message: e.response.data.message,
            data: e.response.data.data,
            errors: e.response.data.errors,
          };
        }

        return {
          ok: false,
          code: 0,
          message: e.message,
          data: {},
          errors: [],
        };
      }

      return {
        ok: false,
        code: -1,
        message: (e as Error).message,
        data: {},
        errors: [],
      };
    }
  }



}

export const http = new Http(import.meta.env.BACKEND_URL);
