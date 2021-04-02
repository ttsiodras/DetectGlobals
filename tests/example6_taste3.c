/* Buildsupport is (c) 2008-2017 European Space Agency
 * contact: maxime.perrotin@esa.int
 * License is LGPL, check LICENSE file */
/* build_ada_skeletons.c

  this program generates empty Ada functions respecting the interfaces defined
  in the interface view. it provides functions to invoke RI.

  Copyright 2014-2015 IB Krates <info@krates.ee>
       QGenc code generator integration
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <assert.h>

#include "my_types.h"
#include "practical_functions.h"

static FILE *adb = NULL, *ads = NULL;

/* Adds header to ads and (if new) adb files */
int ada_gw_preamble(FV * fv)
{
    int hasparam = 0;

    /* todo: move the modules list to the FV struct */
    ASN1_Module_list *modules = NULL;

    if (NULL == ads)
        return -1;

    /* a. ads preamble */
    fprintf(ads,
            "-- This file was generated automatically: DO NOT MODIFY IT !\n\n");
    fprintf(ads,
            "-- Declaration of the provided and required interfaces\n\n");
    fprintf(ads, "--  pragma style_checks (off);\n");
    fprintf(ads, "--  pragma warnings (off);\n");

    /* Check if any interface needs Asn.1 types and if so, include asn1 modules */

    if (NULL != fv->timer_list || get_context()->polyorb_hi_c) {
       fprintf(ads, "with TASTE_Basictypes;\n"
                    "use  TASTE_Basictypes;\n\n");
    }

    FOREACH(i, Interface, fv->interfaces, {
            CheckForAsn1Params(i, &hasparam);}
    );
    if (hasparam) {
        fprintf(ads, "with AdaASN1RTL;\n");
        fprintf(ads, "use AdaASN1RTL;\n\n");

        /* Build the list of Ada packages to include from the ASN.1 module list */
        FOREACH(i, Interface, fv->interfaces, {
            FOREACH(p, Parameter, i->in, ADD_TO_SET(ASN1_Module, modules, p->asn1_module));
            FOREACH(p, Parameter, i->out, ADD_TO_SET(ASN1_Module, modules, p->asn1_module));
            FOREACH(cp, Context_Parameter, fv->context_parameters, {
                if (strcmp (cp->type.name, "Taste-directive") &&
                    strcmp (cp->type.name, "Simulink-Tunable-Parameter") &&
                    strcmp (cp->type.name, "Timer")) {
                    ADD_TO_SET(ASN1_Module,
                               modules,
                               asn2underscore(cp->type.module, strlen(cp->type.module)));
                }
            });
        });

        FOREACH(m, ASN1_Module, modules, {
                fprintf(ads, "with %s;\nuse %s;\n\n", m, m);}
        );
    }
    if (NULL != fv->instance_of) {
        fprintf(ads, "with %s;\n\n", fv->instance_of);
    }

    if(has_context_param(fv)) {
        fprintf(ads,
                "--  Context Parameters defined in interface view\n"
                "with context_%s;\n\n",
                fv->name);
    }

    fprintf(ads, "package %s is\n", fv->name);

    /* Expose each context parameter - pragma export used by SMP2 */
    FOREACH (cp, Context_Parameter, fv->context_parameters, {
        if (strcmp (cp->type.name, "Taste-directive") &&
            strcmp (cp->type.name, "Simulink-Tunable-Parameter") &&
            strcmp (cp->type.name, "Timer")) {

            fprintf(ads,
                "   %s : asn1Scc%s := Context_%s.%s_Ctxt.%s;\n"
                "   pragma Export(C, %s, \"%s_%s\");\n",
                cp->name,
                asn2underscore(cp->type.name, strlen(cp->type.name)),
                fv->name,
                fv->name,
                cp->name,
                cp->name,
                fv->name,
                cp->name);
        }
    });
    fprintf(ads, "\n");


    /* b. adb preamble (if applicable) */
    if (NULL != adb) {
        fprintf(adb, "--  User implementation of the %s function\n",
                fv->name);
        fprintf(adb,
                "--  This file will never be overwritten once edited and modified\n");
        fprintf(adb,
                "--  Only the interface of functions is regenerated (in the .ads file)\n\n");

        fprintf(adb, "--  pragma style_checks (off);\n");
        fprintf(adb, "--  pragma warnings (off);\n");

        if (hasparam) {
            fprintf(adb, "with AdaASN1RTL;\n");
            fprintf(adb, "use AdaASN1RTL;\n\n");
            FOREACH(m, ASN1_Module, modules, {
                    fprintf(adb, "with %s;\nuse %s;\n\n", m, m);}
            );
        }

        if (qgenada == fv->language) {
            /* Add a with and use clause for every QGenAda PI */
            FOREACH(i, Interface, fv->interfaces, {
                switch (i->direction) {
                    case PI: fprintf(adb, "with %s;\nuse %s;\n\n", i->name, i->name); break;
                    case RI: break;
                    default: break;
                }
            });
        }

        fprintf(adb, "package body %s is\n\n", fv->name);

    }
    return 0;
}

/* Creates FV.ads, and if necessary FV.adb (if it did not already exist) */
int Init_Ada_GW_Backend(FV * fv)
{
    char *path = NULL;
    char *filename = NULL;

    if (NULL != fv->system_ast->context->output) {
        build_string(&path, fv->system_ast->context->output,
                     strlen(fv->system_ast->context->output));
    }

    build_string(&path, fv->name, strlen(fv->name));

    build_string(&filename, fv->name, strlen(fv->name));
    build_string(&filename, ".ads", strlen(".ads"));
    create_file(path, filename, &ads);

    filename[strlen(filename) - 1] = 'b';       /* change from ads to adb */

    if (!file_exists(path, filename)) {
        create_file(path, filename, &adb);
        assert(NULL != adb);
    } else
        INFO ("[INFO] User code not overwritten for function %s\n",
               fv->name);

    free(path);
    free(filename);

    assert(NULL != ads);

    ada_gw_preamble(fv);

    return 0;
}


void close_ada_gw_files(FV * fv)
{
    if (NULL != ads) {
        fprintf(ads, "\nend %s;\n", fv->name);
        close_file(&ads);
    }
    if (NULL != adb) {
        fprintf(adb, "\nend %s;\n", fv->name);
        close_file(&adb);
    }
}

/* Create a string in the form "name: access type",
 * as expected by Ada for list of parameters*/
void Create_Ada_Access_Param(Parameter * p, char **result)
{
    if (NULL != *result) {
        build_string(result, "; ", 2);
    }
    build_string(result, p->name, strlen(p->name));
    build_string(result, ": access Asn1Scc", strlen(": access asn1scc"));
    build_string(result, p->type, strlen(p->type));
}

/*
   Add a Provided interface. Can contain in and out parameters
   Write in ads the declaration of the user functions
   and if adb is new, copy these declarations there too.
*/
void add_PI_to_Ada_gw(Interface * i)
{
    char *ada_params = NULL;

    if (NULL == ads)
        return;

    fprintf(ads,
            "   --  ----------------------------------------------------  --\n"
            "   --  Provided interface \"%s\"\n"
            "   --  ----------------------------------------------------  --\n"
            "   procedure %s",
            i->name,
            i->name);

    /* Create the list of parameters
     * (e.g. "param1: in type1; param2: out type2") */
    FOREACH(p, Parameter, i->in, {
            Create_Ada_Access_Param(p, &ada_params);}
    );

    FOREACH(p, Parameter, i->out, {
            Create_Ada_Access_Param(p, &ada_params);}
    );

    if (NULL != ada_params) {
        fprintf(ads, "(");
        fprintf(ads, "%s", ada_params);
        fprintf(ads, ")");
    }

    fprintf(ads, ";\n");
    fprintf(ads, "   pragma Export(C, %s, \"%s_PI_%s\");\n\n", i->name,
            i->parent_fv->name, i->name);

    if (NULL != adb) {
        fprintf(adb,
                "   --  ------------------------------------------------  --\n"
                "   --  Provided interface \"%s\"\n"
                "   --  ------------------------------------------------  --\n"
                "   procedure %s",
                i->name,
                i->name);
    }

    if (NULL != ada_params && NULL != adb) {
        fprintf(adb, "(");
        fprintf(adb, "%s", ada_params);
        fprintf(adb, ")");
    }

    if (NULL != adb) {
        fprintf(adb,
            " is\n   pragma Suppress (All_Checks);"
            "\n   begin\n\n");

        fprintf(adb,
            "      null;"
            " --  Replace \"null\" with your own code!\n\n   end %s;\n\n",
            i->name);
    }

    if (NULL != ada_params) {
        free(ada_params);
        ada_params = NULL;
    }
}

/* Declaration of the RI in the ads file */
void add_RI_to_Ada_gw(Interface * i)
{
    char *ada_params = NULL;

    if (NULL == ads)
        return;

    fprintf(ads,
            "   --  --------------------------------------------------- --\n"
            "   --  Required interface \"%s\"\n"
            "   --  --------------------------------------------------- --\n"
            "   procedure %s",
            i->name,
            i->name);

    /* Create the list of parameters
     * (e.g. "param1: in type1; param2: out type2") */
    FOREACH(p, Parameter, i->in, {
            Create_Ada_Access_Param(p, &ada_params);}
    );

    FOREACH(p, Parameter, i->out, {
            Create_Ada_Access_Param(p, &ada_params);}
    );

    if (NULL != ada_params) {
        fprintf(ads, "(%s)", ada_params);
    }


    fprintf(ads, ";\n");

    fprintf(ads, "   pragma Import(C, %s, \"%s_RI_%s\");\n", i->name,
            i->parent_fv->name, i->name);

    fprintf(ads, "   procedure RIÜ%s", i->name);
    if (NULL != ada_params) {
        fprintf(ads, "(%s)", ada_params);
    }
    fprintf(ads, " renames %s;\n\n", i->name);

    free(ada_params);
    ada_params = NULL;
}

/* Add timer declarations to the Ada code skeletons */
void Ada_Add_timers (FV *fv)
{
    if (NULL == ads) return;

    if (NULL != fv->timer_list) {
        fprintf (ads, 
                "   --  ------------------------------------------------  --\n"
                "   --                  Timers management                 --\n"
                "   --  ------------------------------------------------  --\n"
                "\n\n");
    }
    FOREACH(timer, String, fv->timer_list, {
        fprintf(ads,
            "   --  This function is called when the timer \"%s\" expires\n"
            "   procedure %s;\n"
            "   pragma Export(C, %s, \"%s_PI_%s\");\n\n"
            "   -- Call this function to set (enable) the timer\n"
            "   -- Value is in milliseconds, and must be a multiple of 100\n"
            "   procedure Set_%s(val: access asn1sccT_UInt32);\n\n"
            "   pragma Import(C, Set_%s, \"%s_RI_SET_%s\");\n\n"
            "   -- Call this function to reset (disable) the timer\n"
            "   procedure Reset_%s;\n\n"
            "   pragma Import(C, Reset_%s, \"%s_RI_RESET_%s\");\n\n",
            timer,
            timer,
            timer,
            fv->name,
            timer,
            timer,
            timer,
            fv->name,
            timer,
            timer,
            timer,
            fv->name,
            timer);
        if (NULL != adb) {
            fprintf(adb,
              "   -- This function is called when the timer \"%s\" expires \n"
              "   procedure %s is\n"
              "   begin\n"
              "       null;  --  Replace \"null\" with your own code!\n"
              "   end;\n\n",
              timer,
              timer);
        }
    });
}


/* Handle instanciation of generic packages */
void Ada_Add_Instanciation(FV *fv) {
    if (NULL == ads) return;

    char *decl = make_string("   package %s_Instance is new %s",
                             fv->name,
                             fv->instance_of);

    /* Instantiate the generic with the required interfaces and timers */
    bool comma = false;
    char *params = NULL;
    FOREACH(i, Interface, fv->interfaces, {
        if (RI == i->direction) {
            params = make_string ("%s%sRIÜ%s => %s",
                                  NULL != params ? params: "",
                                  comma ? ", " : "(",
                                  i->name,
                                  i->name);
            comma = true;
        }
    });

    FOREACH(timer, String, fv->timer_list, {
        params = make_string ("%s%sSet_%s => Set_%s, Reset_%s => Reset_%s",
                              NULL != params ? params : "",
                              comma? ", " : "(",
                              timer,
                              timer,
                              timer,
                              timer);
        comma = true;
    });
    if (NULL != params) {
        decl = make_string ("%s%s);", decl, params);
    }
    else {
        decl = make_string ("%s;", decl);
    }

    fprintf(ads, "%s\n", decl);
    free(decl);
}


/* External interface */
void GW_Ada_Backend(FV * fv)
{
    if (fv->system_ast->context->onlycv)
        return;

    if (ada == fv->language || qgenada == fv->language) {

        /* Create the files and add headers */
        Init_Ada_GW_Backend(fv);

        /* Process each interface of the function */
        FOREACH(i, Interface, fv->interfaces, {
            switch (i->direction) {
                case PI: add_PI_to_Ada_gw(i); break;
                case RI: add_RI_to_Ada_gw(i); break;
                default: break;
            }
        });

        /* SDL semantics requires that the state machine checks the
         * input queue of the process before executing continuous signals */
        if(get_context()->polyorb_hi_c) {
            fprintf(ads,
                    "   --  TASTE API to check if the input queue is empty\n"
                    "   procedure Check_Queue(res: access asn1SccT_Boolean);\n"
                    "   pragma Import(C, Check_Queue, \"%s_RI_check_queue\");\n",
                    fv->name);
        }

        // If any timers, add declarations in code skeleton
        Ada_Add_timers(fv);

        // If the function is an instance, instantiate the generic package
        if (NULL != fv->instance_of) {
            Ada_Add_Instanciation(fv);
        }

        /* Write footers and close files */
        close_ada_gw_files(fv);
    }
}
