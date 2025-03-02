import * as React from "react";
import { CourseMaterial, MaterialsAccordionProps } from "../../types";
import { getAllCourseMaterialsAPI } from "../../api";
import { ThreeDots } from "react-loader-spinner";
import { FormattedMessage } from "react-intl";

const COLOUR_PRIMARY = import.meta.env.VITE_REACT_APP_THEME_COLOUR_PRIMARY;

export const MaterialsAccordion: React.FC<MaterialsAccordionProps> = ({
  courseId,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [materials, setMaterials] = React.useState<CourseMaterial[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [hasLoaded, setHasLoaded] = React.useState(false);

  const loadMaterials = async () => {
    if (hasLoaded) return;

    setIsLoading(true);
    try {
      const data = await getAllCourseMaterialsAPI(courseId);
      setMaterials(data);
      setHasLoaded(true);
    } catch (error) {
      console.error("Error loading materials:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = () => {
    if (!isOpen && !hasLoaded) {
      loadMaterials();
    }
    setIsOpen(!isOpen);
  };

  return (
    <div className="border-2 border-secondary rounded-lg overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full px-4 py-3 text-left bg-white hover:bg-secondary flex justify-between items-center"
      >
        <span className="font-medium text-sm text-primary">
          <FormattedMessage id="configuration.viewIncludedMaterials" />
        </span>
        <br />
        <span className="text-sm leading-normal text-primary">
          <FormattedMessage id="configuration.materialsDescription" />
        </span>
        <svg
          className={`w-5 h-5 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div
          className="p-4"
          style={{ backgroundColor: "rgba(255, 255, 255, 0.3)" }}
        >
          {isLoading ? (
            <div className="flex justify-center p-4">
              <ThreeDots
                height="30"
                width="30"
                radius="9"
                color={COLOUR_PRIMARY}
                ariaLabel="loading-materials"
              />
            </div>
          ) : (
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {materials.length === 0 ? (
                <p className="text-sm text-primary text-center">
                  <FormattedMessage id="configuration.noMaterialsFound" />
                </p>
              ) : (
                materials.map((material, index) => (
                  <div
                    key={index}
                    className="flex items-center py-2 px-3 bg-white rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors duration-200"
                  >
                    <a
                      href={material.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline flex-grow cursor-pointer truncate mr-2"
                    >
                      {material.document_name}
                    </a>
                    <svg
                      className="w-4 h-4 text-primary flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
