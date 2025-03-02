import * as React from "react";
import { FormattedMessage } from "react-intl";
import loadingGif from "../../assets/loading.gif";

export const LoadingMessage: React.FC = () => {
  return (
    <div className="flex flex-col w-full text-sm text-primary max-md:max-w-full pb-4">
      <div className="self-start p-[2px] rounded-lg bg-gradient-to-r from-[#FF86E1] to-[#89EFFF]">
        <div className="p-2.5 rounded-lg bg-white">
          <img
            src={loadingGif}
            alt="Loading"
            className="inline-block w-6 h-6 mr-2"
          />
          <FormattedMessage id="loading.checkingMaterials" />
        </div>
      </div>
    </div>
  );
};
