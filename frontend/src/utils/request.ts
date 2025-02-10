export class RequestManager {
  private abortController: AbortController | null = null;

  abort() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  getSignal() {
    this.abort(); // Cancel any existing request
    this.abortController = new AbortController();
    return this.abortController.signal;
  }
}

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => Promise<ReturnType<T>>) => {
  let timeout: NodeJS.Timeout;
  let currentPromise: Promise<ReturnType<T>> | null = null;

  return (...args: Parameters<T>): Promise<ReturnType<T>> => {
    if (currentPromise) {
      return currentPromise;
    }

    return new Promise((resolve, reject) => {
      const later = () => {
        timeout = undefined!;
        currentPromise = Promise.resolve(func(...args))
          .then((result) => {
            currentPromise = null;
            resolve(result);
            return result;
          })
          .catch((error) => {
            currentPromise = null;
            reject(error);
            throw error;
          });
      };

      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    });
  };
};
