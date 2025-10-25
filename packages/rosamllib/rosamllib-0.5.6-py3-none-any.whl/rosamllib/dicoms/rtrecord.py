import pydicom


class RTRecord:
    """
    A class for accessing and manipulating DICOM RTRECORD (RT Dose) datasets.

    Parameters
    ----------
    record_dataset : pydicom.Dataset
        The DICOM dataset for the RTRECORD.

    Methods
    -------
    __getattr__(attr)
        Accesses DICOM metadata via dot notation.
    __setattr__(attr, value)
        Sets DICOM metadata attributes via dot notation.
    __dir__()
        Returns a list of available attributes and DICOM metadata keywords.
    dir()
        Custom method to return available DICOM metadata and attributes.
    """

    def __init__(self, record_dataset):
        """
        Initializes the RTRecord object with a DICOM dataset.

        Parameters
        ----------
        record_dataset : pydicom.Dataset
            The DICOM dataset containing the RTRECORD information.
        """
        self.record_dataset = record_dataset

    def __getattr__(self, attr):
        """
        Allows attribute access for DICOM metadata via dot notation.

        Parameters
        ----------
        attr : str
            The attribute being accessed (e.g., 'PatientID').

        Returns
        -------
        str
            The value of the requested DICOM metadata tag.

        Raises
        ------
        AttributeError
            If the attribute is not a valid DICOM keyword or metadata is not found.
        """
        if attr in self.dir():
            return getattr(self.record_dataset, attr)

        # Fallback to raising AttributeError if the attribute doesn't exist
        raise AttributeError(f"'RTRecord' object has no attribute '{attr}'")

    def __setattr__(self, attr, value):
        """
        Allows setting DICOM metadata attributes via dot notation.

        Parameters
        ----------
        attr : str
            The attribute being set (e.g., 'PatientID').
        value : str
            The value to be assigned to the attribute.

        Raises
        ------
        AttributeError
            If the attribute is not a valid DICOM keyword or if setting fails.
        """
        if attr == "record_dataset":
            # Avoid recursion by setting the record_dataset directly
            super().__setattr__(attr, value)
            return

        try:
            # Try to find the corresponding DICOM tag for the keyword
            tag = pydicom.datadict.tag_for_keyword(attr)
            if tag is not None:
                tag_obj = pydicom.tag.Tag(tag)
                tag_str = f"{tag_obj.group:04X}|{tag_obj.element:04X}"
                self.record_dataset[tag_str].value = value
            else:
                # If it's not a valid DICOM tag, set it as a regular attribute
                super().__setattr__(attr, value)
        except Exception:
            # If anything goes wrong, fall back to setting the attribute normally
            super().__setattr__(attr, value)

    def __dir__(self):
        """
        Returns a list of attributes and DICOM metadata keywords.

        Returns
        -------
        list
            A combined list of attributes and DICOM metadata keywords.
        """
        default_dir = super().__dir__()
        dicom_keywords = [
            pydicom.datadict.keyword_for_tag(tag) for tag in self.record_dataset.keys()
        ]
        dicom_keywords = [keyword for keyword in dicom_keywords if keyword]  # Filter out None

        # Combine the default attributes with the DICOM keywords
        return default_dir + dicom_keywords

    def dir(self):
        """
        Custom dir method to return a list of available attributes and DICOM metadata keywords.

        Returns
        -------
        list of str
            List of all attributes, including DICOM metadata keywords.
        """
        return self.__dir__()
