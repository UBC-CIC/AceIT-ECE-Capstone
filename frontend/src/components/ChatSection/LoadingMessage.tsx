import * as React from "react";
import loadingGif from "../../assets/loading.gif";

export const LoadingMessage: React.FC = () => {
  return (
    <div className="flex flex-col w-full text-sm text-indigo-950 max-md:max-w-full">
      <div className="self-start p-[2px] rounded-lg bg-gradient-to-r from-[#FF86E1] to-[#89EFFF]">
        <div className="p-2.5 rounded-lg bg-white">
          <img
            src={loadingGif}
            alt="Loading"
            className="inline-block w-6 h-6 mr-2"
          />
          Checking Course Materials
        </div>
      </div>
    </div>
  );
};
