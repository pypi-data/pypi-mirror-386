import { IPublicClientApplication } from "@azure/msal-browser";
import {
  UseMutateAsyncFunction,
  UseMutateFunction,
} from "@tanstack/react-query";
import {
  AxiosError,
  AxiosResponse,
  AxiosResponseHeaders,
  RawAxiosResponseHeaders,
} from "axios";
import { Dispatch, SetStateAction } from "react";
import { toast } from "react-toastify";

import {
  Message,
  Options,
  SessionCreateSessionData,
  SessionPatchAccessTokenData,
} from "#client";
import { ssoScopes } from "#config";
import { getStorageItem, removeStorageItem, setStorageItem } from "./storage";

const FRAGMENTTOKEN_PREFIX = "#token=";
const STORAGENAME_TOKEN = "apiToken";
const APITOKEN_HEADER = "x-fmu-settings-api";
const UPSTREAMSOURCE_HEADER = "x-upstream-source";
const APIURL_SESSION = "/api/v1/session/";

export type TokenStatus = {
  present?: boolean;
  valid?: boolean;
};

function getTokenFromFragment() {
  const fragment = location.hash;
  if (fragment !== "" && fragment.startsWith(FRAGMENTTOKEN_PREFIX)) {
    return fragment.substring(FRAGMENTTOKEN_PREFIX.length);
  } else {
    return "";
  }
}

function getTokenFromStorage() {
  return getStorageItem(sessionStorage, STORAGENAME_TOKEN) ?? "";
}

function setTokenInStorage(token: string) {
  setStorageItem(sessionStorage, STORAGENAME_TOKEN, token);
}

export function removeTokenFromStorage() {
  removeStorageItem(sessionStorage, STORAGENAME_TOKEN);
}

export function getApiToken() {
  const fragmentToken = getTokenFromFragment();
  const storageToken = getTokenFromStorage();
  if (fragmentToken !== "") {
    setTokenInStorage(fragmentToken);
    history.pushState(
      null,
      "",
      window.location.pathname + window.location.search,
    );

    return fragmentToken;
  } else if (storageToken !== "") {
    return storageToken;
  } else {
    return "";
  }
}

export function isApiTokenNonEmpty(apiToken: string) {
  return apiToken !== "";
}

export function isApiUrlSession(url?: string): boolean {
  return url === APIURL_SESSION;
}

export function isExternalApi(
  headers: RawAxiosResponseHeaders | AxiosResponseHeaders | undefined,
) {
  return headers && headers[UPSTREAMSOURCE_HEADER] === "SMDA";
}

export async function createSessionAsync(
  createSessionMutateAsync: UseMutateAsyncFunction<
    Message,
    AxiosError,
    Options<SessionCreateSessionData>
  >,
  apiToken: string,
) {
  await createSessionMutateAsync({
    headers: { [APITOKEN_HEADER]: apiToken },
  });
}

export function handleSsoLogin(msalInstance: IPublicClientApplication) {
  try {
    void msalInstance.loginRedirect({ scopes: ssoScopes });
  } catch (error) {
    console.error("Error when logging in to SSO: ", error);
    toast.error(String(error));
  }
}

export function handleAddSsoAccessToken(
  patchAccessTokenMutate: UseMutateFunction<
    Message,
    AxiosError,
    Options<SessionPatchAccessTokenData>
  >,
  accessToken: string,
) {
  patchAccessTokenMutate({ body: { id: "smda_api", key: accessToken } });
}

export const responseInterceptorFulfilled =
  (
    apiTokenStatusValid: boolean,
    setApiTokenStatus: Dispatch<SetStateAction<TokenStatus>>,
  ) =>
  (response: AxiosResponse): AxiosResponse => {
    if (isApiUrlSession(response.config.url) && !apiTokenStatusValid) {
      setApiTokenStatus((apiTokenStatus) => ({
        ...apiTokenStatus,
        valid: true,
      }));
    }

    return response;
  };

export const responseInterceptorRejected =
  (
    apiToken: string,
    setApiToken: Dispatch<SetStateAction<string>>,
    apiTokenStatusValid: boolean,
    setApiTokenStatus: Dispatch<SetStateAction<TokenStatus>>,
    setRequestSessionCreation: Dispatch<SetStateAction<boolean>>,
  ) =>
  async (error: AxiosError) => {
    if (error.status === 401) {
      if (isApiUrlSession(error.response?.config.url)) {
        if (isApiTokenNonEmpty(apiToken)) {
          setApiToken(() => "");
          removeTokenFromStorage();
        }
        if (apiTokenStatusValid) {
          setApiTokenStatus(() => ({}));
        }
      } else if (!isExternalApi(error.response?.headers)) {
        setRequestSessionCreation(true);
      }
    }

    return Promise.reject(error);
  };
