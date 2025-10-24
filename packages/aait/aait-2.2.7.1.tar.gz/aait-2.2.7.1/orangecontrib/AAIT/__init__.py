import Orange
from packaging import version
target_version = version.parse("3.37")
current_version = version.parse(Orange.version.version)
if current_version < target_version: # Skip the file
    print("Orange version not compatible with all of AAIT functions !")


else: # Execute the file
    import os
    import tempfile
    import gc
    import sys
    from orangewidget.workflow.discovery import WidgetDiscovery
    #from orangecanvas.registry import CategoryDescription
    from orangecanvas.registry.utils import category_from_package_globals
    from orangecanvas.utils.pkgmeta import get_distribution




    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\","/"):
         from Orange.widgets.orangecontrib.AAIT.utils.tools import first_time_check # ignore pyflakes alert
         from Orange.widgets.orangecontrib.AAIT.utils import MetManagement
    else:
         from orangecontrib.AAIT.utils.tools import first_time_check # ignore pyflakes alert
         from orangecontrib.AAIT.utils import MetManagement


    def remove_temp_file():
        """
        remove file which allows a message box to be displayed “launch of orange software”
        """
        temp_folder = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_folder, 'orange_lance.txt')
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier temporaire : {e}")



    def find_widget_discovery_objects():
        """
        return a list of WidgetDiscovery isntance based on garbage collector parsing
        """
        gc.collect()
        objects = gc.get_objects()
        widget_discoveries = [obj for obj in objects if isinstance(obj, WidgetDiscovery)]
        return widget_discoveries

    def import_proprietary_categories():
        # Utilisation de la fonction pour obtenir les objets
        widget_discoveries = find_widget_discovery_objects()
        the_discovery = None
        for widget in widget_discoveries:
            the_discovery = widget
        if the_discovery is None:
            return
        pkgs = MetManagement.get_category_extension_to_load()
        if len(pkgs)==0:
            return
        sys.path.append(MetManagement.get_widget_extension_path())
        dist = get_distribution("Orange3")
        for pkg in pkgs:
            the_discovery.handle_category(category_from_package_globals(pkg))
        for pkg in pkgs:
            the_discovery.process_category_package(pkg, distribution=dist)

    def duplicate_widget_if_needed_exept_POW_file():
        path_to_check=os.path.dirname(__file__)+"/widgets"
        path_to_check=path_to_check.replace("\\","/")
        files_py = [f for f in os.listdir(path_to_check) if f.endswith('.py')]


        files_py_duplicated=[]
        files_py_not_duplicated=[]
        for element in files_py:
            if element[:2]=="__":
                files_py_duplicated.append(element)
                continue
            files_py_not_duplicated.append(element)
        for element in files_py_duplicated:
            if element=="__init__.py":
                continue
            file_origine=(element.split("__" )[-1])
            if not os.path.isfile(path_to_check+"/"+file_origine):
                try:
                    os.remove(path_to_check+"/"+element)
                    continue
                except Exception as e:
                    print(f"Error : {e}")
            if MetManagement.get_size(path_to_check+"/"+file_origine)!=MetManagement.get_size(path_to_check+"/"+element):
                # Paths to the two files
                file_1 = path_to_check+"/"+file_origine
                file_2 = path_to_check+"/"+element

                try:
                    # Read the content of the first file
                    with open(file_1, 'r') as source_file:
                        content = source_file.read()

                    # Write the content into the second file
                    with open(file_2, 'w') as target_file:
                        target_file.write(content)

                    print(f"The file '{file_2}' has been overwritten with the content of '{file_1}'.")
                    continue
                except FileNotFoundError as e:
                    print(f"Error: File not found. {e}")
                except PermissionError as e:
                    print(f"Error: Permission denied. {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")


        list_file_to_created=[]
        list_file_to_duplicate=[]
        for extention in MetManagement.get_category_extension_to_load():
            dev=False
            prefix = ""
            # extention_a_jouter=extention
            if len(extention) > 4:
                if extention[:3]=="dev":
                    prefix="__dev"
                    dev=True
                    # case not dev  and dev module required
                    if "site-packages/Orange/widgets" not in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
                        continue
            # case dev  and not dev module required
            if dev == False:
                if "site-packages/Orange/widgets"  in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
                    continue
            prefix+="__"+extention+"__"
            dir_to_check=MetManagement.get_widget_extension_path()+extention+"/"
            files_py = [f for f in os.listdir(dir_to_check) if f.endswith('.py')]
            for ffile in files_py:
                if ffile=="__init__.py":
                    continue
                if ffile[:3]!="POW":
                    if ffile in files_py_not_duplicated:
                        list_file_to_created.append(prefix+ffile)
                        list_file_to_duplicate.append(ffile)
                    continue


        # remove unusuable files
        for element in files_py_duplicated:
            if element =="__init__.py":
                continue
            if element in list_file_to_created:
                continue
            try:
                print("remove ",path_to_check + "/" + element)
                os.remove(path_to_check + "/" + element)
            except Exception as e:
                print(f"Error : {e}")

        for i in range(len(list_file_to_created)):
            #print(list_file_to_created[i]," ",list_file_to_duplicate[i])
            file_1 = path_to_check + "/" + list_file_to_duplicate[i]
            file_2 = path_to_check + "/" + list_file_to_created[i]
            if os.path.isfile(file_2):
                #print(file_2 ,"existe")
                continue

            try:
                # Read the content of the first file
                with open(file_1, 'r') as source_file:
                    content = source_file.read()

                # Write the content into the second file
                with open(file_2, 'w') as target_file:
                    target_file.write(content)

                print(f"The file '{file_2}' has been overwritten with the content of '{file_1}'.")
                continue
            except FileNotFoundError as e:
                print(f"Error: File not found. {e}")
            except PermissionError as e:
                print(f"Error: Permission denied. {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    def duplicate_POW_file():
        path_to_check=os.path.dirname(__file__)+"/widgets"
        path_to_check=path_to_check.replace("\\","/")
        files_py = [f for f in os.listdir(path_to_check) if f.endswith('.py') and f.startswith('POW')]
        # update pow file if necessary
        original_element="POW_Wfactory.py"
        original_pow_file=path_to_check+"/"+original_element
        if False==os.path.isfile(original_pow_file):
            print(original_element +"does not exist")
            return
        files_py_duplicated=[]
        for element in files_py:
            if element!=original_element:
                files_py_duplicated.append(element)
            if MetManagement.get_size(original_pow_file) != MetManagement.get_size(
                    path_to_check + "/" + element):
                # Paths to the two files
                file_1 = original_pow_file
                file_2 = path_to_check + "/" + element
                try:
                    # Read the content of the first file
                    with open(file_1, 'r') as source_file:
                        content = source_file.read()

                    # Write the content into the second file
                    with open(file_2, 'w') as target_file:
                        target_file.write(content)

                    print(f"The file '{file_2}' has been overwritten with the content of '{file_1}'.")
                    continue
                except FileNotFoundError as e:
                    print(f"Error: File not found. {e}")
                except PermissionError as e:
                    print(f"Error: Permission denied. {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
        list_file_to_created = []
        list_file_to_duplicate = []

        for extention in MetManagement.get_category_extension_to_load():
            dev = False
            suffix = ""
            if len(extention) > 4:
                if extention[:3] == "dev":
                    suffix = "__dev"
                    dev = True
                    # case not dev  and dev module required
                    if "site-packages/Orange/widgets" not in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
                        continue
            # case dev  and not dev module required
            if dev == False:
                if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
                    continue
            suffix+="__"+extention+"__"
            dir_to_check=MetManagement.get_widget_extension_path()+extention+"/"
            files_py = [f for f in os.listdir(dir_to_check) if f.endswith('.py') and f.startswith('POW')]
            for ffile in files_py:
                list_file_to_created.append(ffile[:-3]+suffix+".py")
                list_file_to_duplicate.append(original_element)
        # remove unusuable files
        for element in files_py_duplicated:
            if element in list_file_to_created:
                continue
            try:
                print("remove ",path_to_check + "/" + element)
                os.remove(path_to_check + "/" + element)
            except Exception as e:
                print(f"Error : {e}")
        for i in range(len(list_file_to_created)):
            #print(list_file_to_created[i]," ",list_file_to_duplicate[i])
            file_1 = path_to_check + "/" + list_file_to_duplicate[i]
            file_2 = path_to_check + "/" + list_file_to_created[i]
            if os.path.isfile(file_2):
                #print(file_2 ,"existe")
                continue

            try:
                # Read the content of the first file
                with open(file_1, 'r') as source_file:
                    content = source_file.read()

                # Write the content into the second file
                with open(file_2, 'w') as target_file:
                    target_file.write(content)

                print(f"The file '{file_2}' has been overwritten with the content of '{file_1}'.")
                continue
            except FileNotFoundError as e:
                print(f"Error: File not found. {e}")
            except PermissionError as e:
                print(f"Error: Permission denied. {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    # remove the file in temp folder
    remove_temp_file()
    import_proprietary_categories()
    duplicate_widget_if_needed_exept_POW_file()

    duplicate_POW_file()