import * as React from "react";
import { CourseMaterial, MaterialsAccordionProps } from "../../types";
import { getAllCourseMaterialsAPI } from "../../api";
import { ThreeDots } from "react-loader-spinner";
import { FormattedMessage } from "react-intl";

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
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
      >
        <span className="font-medium text-sm text-indigo-950">
          <FormattedMessage id="configuration.viewIncludedMaterials" />
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
        <div className="p-4">
          {isLoading ? (
            <div className="flex justify-center p-4">
              <ThreeDots
                height="30"
                width="30"
                radius="9"
                color="#1e1b4b"
                ariaLabel="loading-materials"
              />
            </div>
          ) : (
            <div className="space-y-2">
              {materials.length === 0 ? (
                <p className="text-sm text-gray-500 text-center">
                  <FormattedMessage id="configuration.noMaterialsFound" />
                </p>
              ) : (
                materials.map((material, index) => (
                  <div
                    key={index}
                    className="text-sm p-2 hover:bg-gray-50 rounded"
                  >
                    <a
                      href={material.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:text-indigo-800"
                    >
                      {material.name}
                    </a>
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
