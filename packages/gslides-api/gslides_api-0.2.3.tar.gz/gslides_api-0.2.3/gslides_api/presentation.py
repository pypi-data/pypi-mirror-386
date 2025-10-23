import copy
import logging
from typing import Any, Dict, List, Optional

from pydantic import model_validator

from gslides_api.client import GoogleAPIClient, api_client
from gslides_api.domain.domain import GSlidesBaseModel, Size
from gslides_api.element.base import ElementKind
from gslides_api.element.element import PageElement
from gslides_api.page.page import Layout, Master, NotesMaster, Page
from gslides_api.page.slide import Slide

logger = logging.getLogger(__name__)


class Presentation(GSlidesBaseModel):
    """Represents a Google Slides presentation."""

    presentationId: Optional[str]
    pageSize: Size
    slides: Optional[List[Slide]] = None
    title: Optional[str] = None
    locale: Optional[str] = None
    revisionId: Optional[str] = None
    masters: Optional[List[Master]] = None
    layouts: Optional[List[Layout]] = None
    notesMaster: Optional[NotesMaster] = None

    @classmethod
    def create_blank(
        cls,
        title: str = "New Presentation",
        api_client: Optional[GoogleAPIClient] = None,
    ) -> "Presentation":
        """Create a blank presentation in Google Slides."""
        client = api_client or globals()["api_client"]
        new_id = client.create_presentation({"title": title})
        return cls.from_id(new_id, api_client=api_client)

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "Presentation":
        """
        Convert a JSON representation of a presentation into a Presentation object.

        Args:
            json_data: The JSON data representing a Google Slides presentation

        Returns:
            A Presentation object populated with the data from the JSON
        """
        # Use Pydantic's model_validate to parse the processed JSON
        out = cls.model_validate(json_data)

        # Set presentation_id on slides
        if out.slides is not None:
            for s in out.slides:
                s.presentation_id = out.presentationId

        return out

    @classmethod
    def from_id(
        cls, presentation_id: str, api_client: Optional[GoogleAPIClient] = None
    ) -> "Presentation":
        client = api_client or globals()["api_client"]
        presentation_json = client.get_presentation_json(presentation_id)
        return cls.from_json(presentation_json)

    def copy_via_domain_objects(
        self, api_client: Optional[GoogleAPIClient] = None
    ) -> "Presentation":
        """Clone a presentation in Google Slides."""
        client = api_client or globals()["api_client"]
        config = self.to_api_format()
        config.pop("presentationId", None)
        config.pop("revisionId", None)
        new_id = client.create_presentation(config)
        return self.from_id(new_id, api_client=api_client)

    def copy_via_drive(
        self,
        copy_title: Optional[str] = None,
        api_client: Optional[GoogleAPIClient] = None,
        folder_id: Optional[str] = None,
    ):
        client = api_client or globals()["api_client"]
        copy_title = copy_title or f"Copy of {self.title}"
        new = client.copy_presentation(
            self.presentationId, copy_title, folder_id=folder_id
        )
        return self.from_id(new["id"], api_client=api_client)

    def sync_from_cloud(self, api_client: Optional[GoogleAPIClient] = None):
        re_p = Presentation.from_id(self.presentationId, api_client=api_client)
        self.__dict__ = re_p.__dict__

    def slide_from_id(self, slide_id: str) -> Optional[Page]:
        match = [s for s in self.slides if s.objectId == slide_id]
        if len(match) == 0:
            logger.error(
                f"Slide with id {slide_id} not found in presentation {self.presentationId}"
            )
            return None
        return match[0]

    def delete_slide(self, slide_id: str, api_client: Optional[GoogleAPIClient] = None):
        client = api_client or globals()["api_client"]
        client.delete_object(slide_id, self.presentationId)

    def get_slide_by_name(self, slide_name: str) -> Optional[Slide]:
        for slide in self.slides:
            if slide.speaker_notes.read_text().strip() == slide_name:
                return slide
        return None

    def get_page_elements_from_id(self, element_id: str) -> List[PageElement]:
        out = []

        # Build list of all pages, handling None values
        all_pages = []
        if self.slides:
            all_pages.extend(self.slides)
        if self.layouts:
            all_pages.extend(self.layouts)
        if self.masters:
            all_pages.extend(self.masters)

        for page in all_pages:
            for element in page.page_elements_flat:
                if element.objectId == element_id:
                    out.append(element)
        return out

    @model_validator(mode="after")
    def resolve_placeholder_parents(self) -> "Presentation":
        """Resolve parent_object references for shape placeholders.

        Iterates over all ShapeElements in slides and checks if they have a
        placeholder with a parentObjectId. If so, fetches the parent element
        from elsewhere in the presentation and sets the parent_object reference.
        """
        if not self.slides:
            return self

        for slide in self.slides:
            for element in slide.page_elements_flat:
                if (
                    element.type == ElementKind.SHAPE
                    and hasattr(element, "shape")
                    and element.shape
                    and hasattr(element.shape, "placeholder")
                    and element.shape.placeholder
                    and hasattr(element.shape.placeholder, "parentObjectId")
                    and element.shape.placeholder.parentObjectId
                ):

                    parent_id = element.shape.placeholder.parentObjectId
                    parents = self.get_page_elements_from_id(parent_id)

                    if parents:
                        element.shape.placeholder.parent_object = parents[
                            0
                        ]  # Use first match
                        logger.debug(
                            f"Resolved parent object {parent_id} for placeholder in element {element.objectId}"
                        )
                    else:
                        logger.warning(
                            f"Parent object {parent_id} not found for placeholder in element {element.objectId}"
                        )

        return self

    @property
    def url(self):
        if self.presentationId is None:
            return None
        return f"https://docs.google.com/presentation/d/{self.presentationId}/edit"
